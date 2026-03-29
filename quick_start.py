#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────
#  quick_start.py
#
#  Run this after installing requirements to verify your setup
#  is correct before running the full pipeline.
#
#  Usage:  python quick_start.py
# ─────────────────────────────────────────────────────────────────

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def check(label: str, fn) -> bool:
    try:
        fn()
        console.print(f"  [green]✔[/green]  {label}")
        return True
    except Exception as exc:
        console.print(f"  [red]✗[/red]  {label} — [dim]{exc}[/dim]")
        return False


def main():
    console.print(Panel("[bold cyan]Second Brain — Setup Checker[/bold cyan]", expand=False))
    console.print()

    results = {}

    # ── Python version ────────────────────────────────────────────
    console.print("[bold]Python & core packages[/bold]")
    results["python"] = check(
        f"Python {sys.version_info.major}.{sys.version_info.minor} (need ≥3.10)",
        lambda: (None if sys.version_info >= (3, 10) else (_ for _ in ()).throw(RuntimeError("Need Python 3.10+"))),
    )
    results["dotenv"]    = check("python-dotenv",     lambda: __import__("dotenv"))
    results["rich"]      = check("rich",              lambda: __import__("rich"))
    results["tqdm"]      = check("tqdm",              lambda: __import__("tqdm"))
    results["nest"]      = check("nest_asyncio",      lambda: __import__("nest_asyncio"))

    console.print()
    console.print("[bold]PDF parsing[/bold]")
    results["fitz"]      = check("PyMuPDF (fitz)",    lambda: __import__("fitz"))
    results["pdfplumber"]= check("pdfplumber",        lambda: __import__("pdfplumber"))

    console.print()
    console.print("[bold]Vector store[/bold]")
    results["chromadb"]  = check("chromadb",          lambda: __import__("chromadb"))

    console.print()
    console.print("[bold]LlamaIndex core[/bold]")
    results["li_core"]   = check("llama-index-core",  lambda: __import__("llama_index.core"))
    results["li_chroma"] = check("llama-index-vector-stores-chroma",
                                  lambda: __import__("llama_index.vector_stores.chroma"))
    results["li_hf"]     = check("llama-index-embeddings-huggingface",
                                  lambda: __import__("llama_index.embeddings.huggingface"))

    console.print()
    console.print("[bold]LLM provider[/bold]")

    import config
    console.print(f"  [dim]LLM_PROVIDER = {config.LLM_PROVIDER}[/dim]")

    if config.LLM_PROVIDER == "ollama":
        results["ollama_pkg"] = check("llama-index-llms-ollama",
                                       lambda: __import__("llama_index.llms.ollama"))
        # Try connecting to Ollama
        try:
            import httpx
            r = httpx.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=3)
            models = [m["name"] for m in r.json().get("models", [])]
            if config.OLLAMA_MODEL in " ".join(models):
                console.print(f"  [green]✔[/green]  Ollama running, model '{config.OLLAMA_MODEL}' available")
                results["ollama_running"] = True
            else:
                console.print(f"  [yellow]⚠[/yellow]  Ollama running but '{config.OLLAMA_MODEL}' not found.")
                console.print(f"       Run: [cyan]ollama pull {config.OLLAMA_MODEL}[/cyan]")
                results["ollama_running"] = False
        except Exception:
            console.print(f"  [red]✗[/red]  Ollama not reachable at {config.OLLAMA_BASE_URL}")
            console.print("       Run: [cyan]ollama serve[/cyan]  (in a separate terminal)")
            results["ollama_running"] = False

    elif config.LLM_PROVIDER == "gemini":
        results["gemini_pkg"] = check("llama-index-llms-gemini",
                                       lambda: __import__("llama_index.llms.gemini"))
        if not config.GEMINI_API_KEY:
            console.print("  [red]✗[/red]  GEMINI_API_KEY not set in .env")
            results["gemini_key"] = False
        else:
            console.print(f"  [green]✔[/green]  GEMINI_API_KEY is set")
            results["gemini_key"] = True

    console.print()
    console.print("[bold]Streamlit (UI)[/bold]")
    results["streamlit"] = check("streamlit", lambda: __import__("streamlit"))

    console.print()
    console.print("[bold]Project config[/bold]")
    results["config"] = check("config.py loads",       lambda: __import__("config"))
    results["utils"]  = check("utils package loads",   lambda: __import__("utils"))
    results["agent"]  = check("agent package loads",   lambda: __import__("agent"))

    # Check notes folder
    import config as cfg
    if cfg.NOTES_FOLDER.exists():
        pdfs = list(cfg.NOTES_FOLDER.rglob("*.pdf"))
        console.print(f"  [green]✔[/green]  Notes folder exists ({len(pdfs)} PDFs found)")
        results["notes_folder"] = True
        if not pdfs:
            console.print(f"       [yellow]→ Drop PDF files into: {cfg.NOTES_FOLDER.resolve()}[/yellow]")
    else:
        console.print(f"  [yellow]⚠[/yellow]  Notes folder not found: {cfg.NOTES_FOLDER}")
        console.print("       It will be created when you run ingest.py")
        results["notes_folder"] = False

    # ── Summary ───────────────────────────────────────────────────
    console.print()
    passed = sum(1 for v in results.values() if v)
    total  = len(results)

    if passed == total:
        console.print(Panel(
            "[bold green]✅ All checks passed! You're ready to go.[/bold green]\n\n"
            "Next steps:\n"
            "  1. Drop PDFs into [cyan]data/your_notes_folder/[/cyan]\n"
            "  2. [cyan]python manifest_builder.py[/cyan]\n"
            "  3. [cyan]python ingest.py[/cyan]\n"
            "  4. [cyan]python -m eval.run_eval[/cyan]\n"
            "  5. [cyan]streamlit run ui/app.py[/cyan]",
            expand=False,
        ))
    else:
        failed = [k for k, v in results.items() if not v]
        console.print(Panel(
            f"[bold yellow]⚠ {passed}/{total} checks passed.[/bold yellow]\n\n"
            f"Fix these before proceeding: [red]{', '.join(failed)}[/red]\n\n"
            "See README.md → Troubleshooting for help.",
            expand=False,
        ))


if __name__ == "__main__":
    main()
