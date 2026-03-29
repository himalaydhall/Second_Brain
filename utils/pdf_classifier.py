# ─────────────────────────────────────────────────────────────────
#  utils/pdf_classifier.py
#  Inspects a PDF and decides the best parsing strategy.
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations
import fitz  # PyMuPDF
from pathlib import Path
from rich.console import Console

console = Console()


def classify_pdf(path: str | Path) -> str:
    """
    Classify a PDF into one of three categories:
      - "text"    : mostly machine-readable text → use pdfplumber (free)
      - "scanned" : mostly raster images / no text → use LlamaParse (paid)
      - "mixed"   : combination of both → use LlamaParse for safety

    The heuristic: sample up to 10 evenly spaced pages.
    A page is "text-rich" if it has >50 chars of extractable text.
    """
    path = str(path)
    try:
        doc = fitz.open(path)
        n_pages = len(doc)
        if n_pages == 0:
            return "text"

        # Sample up to 10 pages spread across the document
        step      = max(1, n_pages // 10)
        sample    = list(range(0, n_pages, step))[:10]
        text_rich = 0

        for i in sample:
            page = doc[i]
            txt  = page.get_text().strip()
            if len(txt) > 50:
                text_rich += 1

        ratio = text_rich / len(sample)

        if ratio >= 0.8:
            kind = "text"
        elif ratio <= 0.2:
            kind = "scanned"
        else:
            kind = "mixed"

        doc.close()
        return kind

    except Exception as exc:
        console.print(f"[yellow]⚠ Could not classify {Path(path).name}: {exc}. Defaulting to 'text'.[/yellow]")
        return "text"


def get_page_count(path: str | Path) -> int:
    """Return the number of pages in a PDF without reading the whole file."""
    try:
        doc = fitz.open(str(path))
        n   = len(doc)
        doc.close()
        return n
    except Exception:
        return 0


def extract_fast_text(path: str | Path) -> str:
    """
    Fast full-text extraction using PyMuPDF.
    Suitable for text-native PDFs as a free alternative to LlamaParse.
    Falls back page-by-page so one bad page doesn't kill the whole doc.
    """
    text_parts: list[str] = []
    try:
        doc = fitz.open(str(path))
        for page in doc:
            try:
                text_parts.append(page.get_text())
            except Exception:
                text_parts.append("")
        doc.close()
    except Exception as exc:
        console.print(f"[red]✗ PyMuPDF extraction failed for {Path(path).name}: {exc}[/red]")
    return "\n".join(text_parts)
