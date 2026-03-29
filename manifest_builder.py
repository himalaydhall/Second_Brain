#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────
#  manifest_builder.py
#
#  Run this BEFORE ingest.py.
#  Walks your notes folder, shows each PDF, and lets you assign
#  a date and topic tags interactively.
#
#  Usage:
#    python manifest_builder.py
#    python manifest_builder.py --folder ./data/your_notes_folder
#    python manifest_builder.py --auto   # auto-fill dates from file mtime
# ─────────────────────────────────────────────────────────────────

import argparse
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

import config
from utils import (
    classify_pdf,
    get_page_count,
    load_manifest,
    save_manifest,
    upsert_manifest_entry,
    list_manifest_entries,
)

console = Console()


def auto_build(folder: Path) -> None:
    """Auto-fill manifest using file modification times. No prompts."""
    manifest = load_manifest()
    pdfs = list(folder.rglob("*.pdf"))

    if not pdfs:
        console.print(f"[yellow]No PDFs found in {folder}[/yellow]")
        return

    console.print(f"\n[bold cyan]Auto-building manifest for {len(pdfs)} PDFs...[/bold cyan]\n")

    for pdf in pdfs:
        import os
        mtime      = os.stat(str(pdf)).st_mtime
        date_added = datetime.fromtimestamp(mtime).strftime("%Y-%m")
        manifest[pdf.name] = {
            "date_added": date_added,
            "topics":     [],
            "source":     "pdf",
            "notes":      "",
        }
        console.print(f"  ✔ {pdf.name} → {date_added}")

    save_manifest(manifest)
    console.print(f"\n[green]✅ Manifest saved to {config.MANIFEST_PATH}[/green]")
    console.print("[dim]Tip: edit the manifest manually or re-run without --auto to add topic tags.[/dim]")


def interactive_build(folder: Path) -> None:
    """Walk each PDF and prompt the user for date + topic tags."""
    pdfs     = sorted(folder.rglob("*.pdf"))
    manifest = load_manifest()

    if not pdfs:
        console.print(f"[yellow]No PDFs found in {folder}[/yellow]")
        return

    console.print(f"\n[bold cyan]Found {len(pdfs)} PDFs. Let's tag them.[/bold cyan]")
    console.print("[dim]Press ENTER to accept defaults. Type 'skip' to skip a file.[/dim]\n")

    updated = 0
    for i, pdf in enumerate(pdfs, 1):
        already_in = pdf.name in manifest

        # Show a mini summary
        pages    = get_page_count(pdf)
        pdf_type = classify_pdf(pdf)
        status   = "[green]already in manifest[/green]" if already_in else "[yellow]NEW[/yellow]"

        console.rule(f"[bold]({i}/{len(pdfs)}) {pdf.name}[/bold]")
        console.print(f"  Pages : {pages}   Type: {pdf_type}   Status: {status}")

        if already_in:
            existing = manifest[pdf.name]
            console.print(f"  Current: date={existing.get('date_added')} topics={existing.get('topics')}")
            if not Confirm.ask("  Update this entry?", default=False):
                continue

        # Date
        default_date = (
            manifest[pdf.name].get("date_added", datetime.now().strftime("%Y-%m"))
            if already_in else datetime.now().strftime("%Y-%m")
        )
        date_input = Prompt.ask(
            "  Date added (YYYY-MM)",
            default=default_date,
        )
        if date_input.lower() == "skip":
            continue

        # Topic tags
        default_topics = ",".join(manifest[pdf.name].get("topics", [])) if already_in else ""
        topics_input   = Prompt.ask(
            "  Topic tags (comma-separated, e.g. rag,llm,ethics)",
            default=default_topics,
        )
        topics = [t.strip().lower() for t in topics_input.split(",") if t.strip()]

        # Source
        source_input = Prompt.ask("  Source label (arxiv / book / blog / other)", default="pdf")

        # Notes
        notes_input = Prompt.ask("  One-line note (optional)", default="")

        upsert_manifest_entry(
            filename   = pdf.name,
            date_added = date_input,
            topics     = topics,
            source     = source_input,
            notes      = notes_input,
        )
        updated += 1
        console.print(f"  [green]✔ Saved[/green]\n")

    # Final summary table
    entries = list_manifest_entries()
    table   = Table(title=f"Manifest — {len(entries)} PDFs", show_lines=True)
    table.add_column("Filename",   style="cyan",  no_wrap=True)
    table.add_column("Date",       style="magenta")
    table.add_column("Topics",     style="green")
    table.add_column("Source",     style="yellow")

    for row in entries:
        table.add_row(
            row["filename"],
            row.get("date_added", ""),
            row.get("topics", "") if isinstance(row.get("topics"), str) else ",".join(row.get("topics", [])),
            row.get("source", ""),
        )

    console.print(table)
    console.print(f"\n[green]✅ Done. {updated} entries updated. Manifest at {config.MANIFEST_PATH}[/green]")
    console.print("[bold]Next step:[/bold] run [cyan]python ingest.py[/cyan]")


def main():
    parser = argparse.ArgumentParser(description="Build the PDF manifest for Second Brain")
    parser.add_argument("--folder", default=str(config.NOTES_FOLDER), help="Folder containing your PDFs")
    parser.add_argument("--auto",   action="store_true",              help="Auto-fill dates from file mtime, no prompts")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        console.print(f"[red]Folder not found: {folder}[/red]")
        return

    if args.auto:
        auto_build(folder)
    else:
        interactive_build(folder)


if __name__ == "__main__":
    main()
