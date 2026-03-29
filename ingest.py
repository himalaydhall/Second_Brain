#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────
#  ingest.py
#
#  Phase 1: Parse every PDF in your notes folder and index it
#  into ChromaDB with rich metadata.
#
#  Usage:
#    python ingest.py                     # index all PDFs
#    python ingest.py --reset             # wipe DB and re-index everything
#    python ingest.py --file report.pdf   # index one specific file
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Document, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from rich.console import Console
from rich.progress import track
from rich.panel import Panel

import config
from utils import (
    classify_pdf,
    extract_fast_text,
    get_metadata_for_pdf,
    load_manifest,
)

console = Console()


# ─── Settings ────────────────────────────────────────────────────

def configure_llamaindex():
    """
    Apply global LlamaIndex settings so every component uses the
    same LLM and embedding model without being passed explicitly.
    """
    Settings.llm         = config.get_llm()
    Settings.embed_model = config.get_embed_model()
    Settings.chunk_size  = 512    # smaller chunks = more precise retrieval
    Settings.chunk_overlap = 64


# ─── PDF Loaders ─────────────────────────────────────────────────

def load_text_pdf(pdf_path: Path) -> str:
    """
    Load a text-native PDF using pdfplumber (free, local).
    Falls back to PyMuPDF if pdfplumber fails.
    """
    try:
        import pdfplumber
        parts: list[str] = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
                # Also try to extract tables as markdown
                tables = page.extract_tables()
                for table in tables:
                    rows = []
                    for row in table:
                        cells = [str(c or "").strip() for c in row]
                        rows.append("| " + " | ".join(cells) + " |")
                    if rows:
                        parts.append("\n".join(rows))
        text = "\n\n".join(parts)
        if len(text.strip()) > 100:
            return text
    except Exception as exc:
        console.print(f"[yellow]⚠ pdfplumber failed ({exc}), trying PyMuPDF...[/yellow]")

    # Fallback to PyMuPDF
    return extract_fast_text(pdf_path)


def load_scanned_pdf(pdf_path: Path) -> str:
    """
    Load a scanned / complex PDF using LlamaParse.
    Requires LLAMA_CLOUD_API_KEY in .env.
    Falls back to PyMuPDF with a warning if no key is set.
    """
    if not config.LLAMA_CLOUD_API_KEY:
        console.print(
            f"[yellow]⚠ {pdf_path.name} appears scanned but LLAMA_CLOUD_API_KEY "
            f"is not set. Falling back to PyMuPDF (quality may be lower).[/yellow]"
        )
        return extract_fast_text(pdf_path)

    try:
        from llama_parse import LlamaParse
        parser = LlamaParse(
            api_key     = config.LLAMA_CLOUD_API_KEY,
            result_type = "markdown",  # cleaner for downstream embedding
            verbose     = False,
        )
        docs = parser.load_data(str(pdf_path))
        return "\n\n".join(d.text for d in docs)
    except Exception as exc:
        console.print(f"[yellow]⚠ LlamaParse failed ({exc}), falling back to PyMuPDF.[/yellow]")
        return extract_fast_text(pdf_path)


def load_pdf(pdf_path: Path) -> tuple[str, str]:
    """
    Classify a PDF and route to the right loader.
    Returns (text, pdf_type).
    """
    kind = classify_pdf(pdf_path)
    if kind == "text":
        text = load_text_pdf(pdf_path)
    else:
        # "scanned" or "mixed" → LlamaParse
        text = load_scanned_pdf(pdf_path)
    return text, kind


# ─── Document Builder ─────────────────────────────────────────────

def build_document(pdf_path: Path, manifest: dict) -> Document | None:
    """
    Parse a PDF and return a LlamaIndex Document with full metadata.
    Returns None if the file yields no usable text.
    """
    text, pdf_type = load_pdf(pdf_path)
    if not text or len(text.strip()) < 50:
        console.print(f"[red]✗ {pdf_path.name} produced no usable text. Skipping.[/red]")
        return None

    meta = get_metadata_for_pdf(pdf_path, manifest)
    meta["pdf_type"] = pdf_type

    return Document(text=text, metadata=meta)


# ─── Indexing ─────────────────────────────────────────────────────

def get_chroma_index(reset: bool = False) -> tuple[VectorStoreIndex, chromadb.Collection]:
    """
    Connect to (or create) a persistent ChromaDB collection and
    wrap it in a LlamaIndex VectorStoreIndex.
    """
    config.CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

    db = chromadb.PersistentClient(path=str(config.CHROMA_DB_PATH))

    if reset:
        try:
            db.delete_collection(config.CHROMA_COLLECTION_NAME)
            console.print(f"[yellow]🗑 Existing collection '{config.CHROMA_COLLECTION_NAME}' deleted.[/yellow]")
        except Exception:
            pass

    collection = db.get_or_create_collection(
        name     = config.CHROMA_COLLECTION_NAME,
        metadata = {"hnsw:space": "cosine"},  # cosine similarity is better for semantic search
    )

    vector_store     = ChromaVectorStore(chroma_collection=collection)
    storage_context  = StorageContext.from_defaults(vector_store=vector_store)
    index            = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context = storage_context,
    )

    return index, collection


def already_indexed(collection: chromadb.Collection, filename: str) -> bool:
    """Check if a PDF has already been indexed by looking for its filename in metadata."""
    try:
        results = collection.get(where={"filename": {"$eq": filename}}, limit=1)
        return len(results["ids"]) > 0
    except Exception:
        return False


def ingest_all(folder: Path, reset: bool = False) -> None:
    """Index every PDF in the folder (skips already-indexed ones)."""
    pdfs = sorted(folder.rglob("*.pdf"))
    if not pdfs:
        console.print(f"[yellow]No PDFs found in {folder}[/yellow]")
        console.print(f"[dim]Place your PDF files inside: {folder.resolve()}[/dim]")
        return

    console.print(Panel(
        f"[bold cyan]Second Brain Ingestion[/bold cyan]\n"
        f"Folder : {folder.resolve()}\n"
        f"PDFs   : {len(pdfs)}\n"
        f"Reset  : {'yes – re-indexing everything' if reset else 'no – skipping already-indexed'}",
        expand=False,
    ))

    configure_llamaindex()
    manifest      = load_manifest()
    index, chroma = get_chroma_index(reset=reset)

    successes, skips, failures = 0, 0, 0

    for pdf in track(pdfs, description="Indexing PDFs..."):
        if not reset and already_indexed(chroma, pdf.name):
            console.print(f"  [dim]→ Skipping (already indexed): {pdf.name}[/dim]")
            skips += 1
            continue

        console.print(f"  [cyan]→ Processing:[/cyan] {pdf.name}")
        doc = build_document(pdf, manifest)
        if doc is None:
            failures += 1
            continue

        try:
            # Insert into the index (this triggers chunking + embedding)
            index.insert(doc)
            successes += 1
            console.print(f"    [green]✔ Indexed[/green]  ({doc.metadata.get('pdf_type')}, "
                          f"{doc.metadata.get('date_added')}, "
                          f"topics: {doc.metadata.get('topics') or 'none'})")
        except Exception as exc:
            console.print(f"    [red]✗ Failed to index: {exc}[/red]")
            failures += 1

    console.print(f"\n[bold green]✅ Done.[/bold green]  "
                  f"Indexed: {successes}  |  Skipped: {skips}  |  Failed: {failures}")
    console.print(f"[dim]ChromaDB at: {config.CHROMA_DB_PATH.resolve()}[/dim]")
    console.print("[bold]Next step:[/bold] run [cyan]python -m eval.run_eval[/cyan] to verify, then [cyan]streamlit run ui/app.py[/cyan]")


def ingest_one(pdf_path: Path, reset_file: bool = False) -> None:
    """Index a single PDF file."""
    if not pdf_path.exists():
        console.print(f"[red]File not found: {pdf_path}[/red]")
        return

    configure_llamaindex()
    manifest      = load_manifest()
    index, chroma = get_chroma_index(reset=False)

    if reset_file and already_indexed(chroma, pdf_path.name):
        # Remove old chunks for this file before re-indexing
        try:
            results = chroma.get(where={"filename": {"$eq": pdf_path.name}})
            if results["ids"]:
                chroma.delete(ids=results["ids"])
                console.print(f"[yellow]🗑 Removed {len(results['ids'])} old chunks for {pdf_path.name}[/yellow]")
        except Exception as exc:
            console.print(f"[yellow]⚠ Could not remove old chunks: {exc}[/yellow]")

    console.print(f"[cyan]Processing:[/cyan] {pdf_path.name}")
    doc = build_document(pdf_path, manifest)
    if doc is None:
        return

    index.insert(doc)
    console.print(f"[green]✔ Indexed successfully[/green]")


# ─── Entry point ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest PDFs into Second Brain")
    parser.add_argument("--folder", default=str(config.NOTES_FOLDER), help="Notes folder")
    parser.add_argument("--reset",  action="store_true", help="Wipe DB and re-index everything")
    parser.add_argument("--file",   default=None,        help="Index a single PDF file")
    args = parser.parse_args()

    if args.file:
        ingest_one(Path(args.file), reset_file=args.reset)
    else:
        ingest_all(Path(args.folder), reset=args.reset)


if __name__ == "__main__":
    main()
