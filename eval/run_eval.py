#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────
#  eval/run_eval.py
#
#  Score the agent against your ground-truth test cases.
#  Run with:  python -m eval.run_eval
#             python -m eval.run_eval --verbose
#             python -m eval.run_eval --id simple_001
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations
import argparse
import time
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


from eval.test_cases import TEST_CASES


console = Console()


# ─── Scoring ──────────────────────────────────────────────────────

def score_response(response: str, test_case: dict) -> dict:
    """
    Score a single response against a test case.

    Returns a dict with:
      - keyword_score : fraction of expected keywords found
      - source_found  : True if expected_source is cited (or None if not required)
      - passed        : True if keyword_score >= 0.6
      - missing_kws   : list of keywords not found
    """
    response_lower = response.lower()

    # Keyword check
    kws        = test_case.get("expected_keywords", [])
    found      = [kw for kw in kws if kw.lower() in response_lower]
    missing    = [kw for kw in kws if kw.lower() not in response_lower]
    kw_score   = len(found) / len(kws) if kws else 1.0

    # Source check
    expected_src = test_case.get("expected_source")
    if expected_src:
        src_found = expected_src.lower() in response_lower
    else:
        src_found = None   # not required

    passed = kw_score >= 0.6

    return {
        "keyword_score" : kw_score,
        "source_found"  : src_found,
        "passed"        : passed,
        "found_kws"     : found,
        "missing_kws"   : missing,
    }


# ─── Runner ───────────────────────────────────────────────────────

def run_all(case_ids: list[str] | None, verbose: bool) -> None:
    cases = TEST_CASES
    if case_ids:
        cases = [c for c in cases if c["id"] in case_ids]
        if not cases:
            console.print(f"[red]No cases matched IDs: {case_ids}[/red]")
            return

    console.print(Panel(
        f"[bold cyan]Second Brain — Eval Run[/bold cyan]\n"
        f"Cases : {len(cases)}\n"
        f"Time  : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        expand=False,
    ))

    results = []

    for case in cases:
        console.print(f"\n[bold]Running:[/bold] [{case['id']}] {case['query'][:70]}...")
        t0 = time.time()

        try:
            from agent.workflow import ask_sync
            response = ask_sync(case["query"])
            elapsed  = round(time.time() - t0, 1)
            score    = score_response(response, case)

            status = "[green]✅ PASS[/green]" if score["passed"] else "[red]❌ FAIL[/red]"
            console.print(
                f"  {status}  "
                f"keywords: {score['keyword_score']:.0%}  |  "
                f"time: {elapsed}s"
            )

            if not score["passed"] or verbose:
                if score["missing_kws"]:
                    console.print(f"  [yellow]Missing keywords:[/yellow] {score['missing_kws']}")
                if verbose:
                    console.print(f"\n  [dim]Response preview:[/dim]\n  {response[:400]}...\n")

            results.append({
                "id"      : case["id"],
                "mode"    : case["mode"],
                "query"   : case["query"],
                "passed"  : score["passed"],
                "kw_pct"  : f"{score['keyword_score']:.0%}",
                "elapsed" : f"{elapsed}s",
            })

        except Exception as exc:
            console.print(f"  [red]💥 Exception: {exc}[/red]")
            results.append({
                "id"      : case["id"],
                "mode"    : case["mode"],
                "query"   : case["query"],
                "passed"  : False,
                "kw_pct"  : "0%",
                "elapsed" : "—",
            })

    # Summary Table
    passed_count = sum(1 for r in results if r["passed"])
    total        = len(results)

    table = Table(title=f"Eval Results — {passed_count}/{total} passed", show_lines=True)
    table.add_column("ID",       style="dim",    no_wrap=True)
    table.add_column("Mode",     style="cyan")
    table.add_column("Status",   justify="center")
    table.add_column("Keywords", justify="right")
    table.add_column("Time",     justify="right", style="dim")

    for r in results:
        table.add_row(
            r["id"],
            r["mode"],
            "✅ PASS" if r["passed"] else "❌ FAIL",
            r["kw_pct"],
            r["elapsed"],
        )

    console.print(f"\n")
    console.print(table)

    pct = passed_count / total * 100 if total else 0
    if pct >= 80:
        console.print("[bold green]🎉 Agent is performing well (≥80%).[/bold green]")
    elif pct >= 60:
        console.print("[bold yellow]⚠ Acceptable but improvable (60–79%).[/bold yellow]")
    else:
        console.print("[bold red]🚨 Below threshold (<60%). Check ingestion and prompts.[/bold red]")


def main():
    parser = argparse.ArgumentParser(description="Run Second Brain eval suite")
    parser.add_argument("--id",      nargs="*", help="Specific case IDs to run")
    parser.add_argument("--verbose", action="store_true", help="Show full response previews")
    args = parser.parse_args()
    run_all(args.id, args.verbose)


if __name__ == "__main__":
    main()