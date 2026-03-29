# ─────────────────────────────────────────────────────────────────
#  agent/workflow.py  (rewritten — plain sync, no event loop issues)
#
#  Same logic as before but uses direct synchronous LLM calls
#  instead of LlamaIndex Workflow events.
#  Works reliably on Windows / Python 3.12.
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations
import json
from typing import Optional, Callable

from llama_index.core import Settings

import config
from agent.prompts import (
    CLASSIFY_PROMPT,
    SIMPLE_SYNTHESIS_PROMPT,
    COMPARE_SYNTHESIS_PROMPT,
    CONTRADICT_SYNTHESIS_PROMPT,
    HITL_CLARIFY_PROMPT,
    SUB_QUESTION_SYSTEM_PROMPT,
)
from agent.tools import (
    search_notes,
    search_notes_by_date,
    list_available_periods,
)


# ─── Setup ────────────────────────────────────────────────────────

def _setup():
    Settings.llm         = config.get_llm()
    Settings.embed_model = config.get_embed_model()
    Settings.chunk_size    = 512
    Settings.chunk_overlap = 64

def get_llm_for_mode(mode: str):
    """Use fast small model for simple lookups, big model for reasoning."""
    import os
    if mode == "simple":
        os.environ["GROQ_MODEL"] = "llama-3.1-8b-instant"
    else:
        os.environ["GROQ_MODEL"] = "llama-3.3-70b-versatile"
    # Clear the LRU cache so config picks up the new model
    config.get_llm.cache_clear() if hasattr(config.get_llm, 'cache_clear') else None
    return config.get_llm()


# ─── Step 1: Classify ─────────────────────────────────────────────

def classify_query(llm, query: str) -> str:
    prompt   = CLASSIFY_PROMPT.format(query=query)
    response = llm.complete(prompt)
    mode     = response.text.strip().lower().split()[0]
    if mode not in ("simple", "compare", "contradict"):
        mode = "simple"
    print(f"\n[Agent] Mode: [{mode.upper()}]  <- '{query[:60]}...'")
    return mode


# ─── Step 2a: Simple search ───────────────────────────────────────

def search_simple(query: str) -> str:
    return search_notes(query, top_k=config.TOP_K_SIMPLE)


# ─── Step 2b: Compare search (sub-question decomposition) ─────────

def search_compare(llm, query: str) -> str:
    decompose_prompt = f"{SUB_QUESTION_SYSTEM_PROMPT}\n\nQuery: {query}"
    response         = llm.complete(decompose_prompt)

    try:
        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
        sub_questions: list[str] = json.loads(raw)
        if not isinstance(sub_questions, list):
            raise ValueError
    except Exception:
        sub_questions = [query]


    sub_questions=sub_questions[:3]


    print(f"[Agent] Decomposed into {len(sub_questions)} sub-questions")

    parts: list[str] = []
    for sq in sub_questions:
        result = search_notes(sq, top_k=config.TOP_K_COMPLEX)
        parts.append(f"### Sub-question: {sq}\n{result}")

    return "\n\n".join(parts)


# ─── Step 2c: Contradiction search ────────────────────────────────

def search_contradict(llm, query: str) -> tuple[str, dict]:
    periods_json = list_available_periods()

    pick_prompt = f"""\
The user asked: "{query}"

Available time periods in the note library:
{periods_json}

Pick the TWO periods most relevant to this query.
Reply with ONLY valid JSON like: {{"period_a": "YYYY-MM", "period_b": "YYYY-MM"}}"""

    response = llm.complete(pick_prompt)
    try:
        raw      = response.text.strip().replace("```json", "").replace("```", "").strip()
        periods  = json.loads(raw)
        period_a = periods["period_a"]
        period_b = periods["period_b"]
    except Exception:
        try:
            all_periods = json.loads(periods_json)
            period_b = all_periods[-1]["period"]
            period_a = all_periods[-2]["period"] if len(all_periods) > 1 else period_b
        except Exception:
            return search_notes(query, config.TOP_K_COMPLEX), {}

    print(f"[Agent] Comparing: {period_a}  <->  {period_b}")

    notes_a = search_notes_by_date(query, period_a, 4)
    notes_b = search_notes_by_date(query, period_b, 4)

    context = CONTRADICT_SYNTHESIS_PROMPT.format(
        query    = query,
        period_a = period_a,
        notes_a  = notes_a,
        period_b = period_b,
        notes_b  = notes_b,
    )
    return context, {"period_a": period_a, "period_b": period_b}


# ─── Step 3: Optional HITL ────────────────────────────────────────

def maybe_clarify(llm, mode: str, context: str, query: str,
                  hitl_callback: Optional[Callable]) -> str:
    if mode == "contradict" and hitl_callback and (
        "No notes found" in context or len(context.strip()) < 200
    ):
        prompt    = HITL_CLARIFY_PROMPT.format(conflict_summary=context or query)
        question  = llm.complete(prompt).text.strip()
        answer    = hitl_callback(question)
        context  += f"\n\n=== User clarification ===\nQ: {question}\nA: {answer}"
    return context


# ─── Step 4: Synthesise ───────────────────────────────────────────

def synthesise(llm, mode: str, query: str, context: str) -> str:
    if mode == "simple":
        prompt = SIMPLE_SYNTHESIS_PROMPT.format(query=query, context=context)
    elif mode == "compare":
        prompt = COMPARE_SYNTHESIS_PROMPT.format(query=query, context=context)
    else:
        prompt = context  # contradiction prompt is already fully built

    return llm.complete(prompt).text.strip()


# ─── Main entry point ─────────────────────────────────────────────

def run_query(query: str, hitl_callback: Optional[Callable] = None) -> str:
    """
    Run the full pipeline synchronously and return the final answer.
    This is the main function to call from eval, UI, and scripts.
    """
    _setup()
    
    # Classify with fast model
    classify_llm = config.get_llm()
    mode = classify_query(classify_llm, query)
    
    # Pick right model for the actual work
    llm = get_llm_for_mode(mode)

    if mode == "simple":
        context = search_simple(query)
    elif mode == "compare":
        context = search_compare(llm, query)
    else:
        context, _ = search_contradict(llm, query)

    context = maybe_clarify(llm, mode, context, query, hitl_callback)
    return synthesise(llm, mode, query, context)


# ─── Aliases for backward compatibility ───────────────────────────

def ask_sync(query: str, hitl_callback: Optional[Callable] = None) -> str:
    return run_query(query, hitl_callback)


def build_workflow(hitl_callback: Optional[Callable] = None):
    """Kept for UI compatibility."""
    class _FakeWorkflow:
        def __init__(self, cb):
            self.cb = cb
        def run_sync(self, query: str) -> str:
            return run_query(query, self.cb)
        async def run(self, query: str) -> str:
            return run_query(query, self.cb)
        async def run_async(self, query: str) -> str:
            return run_query(query, self.cb)
    return _FakeWorkflow(hitl_callback)


async def ask(query: str, hitl_callback: Optional[Callable] = None) -> str:
    return run_query(query, hitl_callback)