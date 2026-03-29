# ─────────────────────────────────────────────────────────────────
#  agent/tools.py
#  Custom tools the agent can "pick up and use".
#  Each tool is a plain Python function wrapped by LlamaIndex.
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations
import json
from typing import Optional

import chromadb
from llama_index.core.tools import FunctionTool

import config
from agent.prompts import CONTRADICT_SYNTHESIS_PROMPT


def _get_collection() -> chromadb.Collection:
    db = chromadb.PersistentClient(path=str(config.CHROMA_DB_PATH))
    return db.get_or_create_collection(config.CHROMA_COLLECTION_NAME)


def _embed_query(query: str) -> list[float]:
    """Embed a query using the cached model from config."""
    embed_model = config.get_embed_model()
    return embed_model.get_query_embedding(query)


# ─── Tool 1: Simple Note Search (with reranker) ───────────────────

def search_notes(query: str, top_k: int = 5) -> str:
    """
    Search the PDF note library for passages relevant to a query.
    Results are reranked by semantic relevance before returning.

    Args:
        query : Natural language question or topic.
        top_k : How many passages to return after reranking (default 5).

    Returns:
        Formatted string of relevant passages with source filenames.
    """
    collection = _get_collection()

    # Fetch more candidates so reranker has room to work
    fetch_k = top_k * 3

    try:
        results = collection.query(
            query_embeddings = [_embed_query(query)],
            n_results        = fetch_k,
            include          = ["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        return f"Search failed: {exc}"

    docs  = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    if not docs:
        return "No relevant notes found for this query."

    # ── Rerank ────────────────────────────────────────────────────
    try:
        from llama_index.core.schema import NodeWithScore, TextNode
        from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
        from llama_index.core import QueryBundle

        nodes = [
            NodeWithScore(node=TextNode(text=doc, metadata=meta), score=1 - dist)
            for doc, meta, dist in zip(docs, metas, dists)
        ]

        reranker = FlagEmbeddingReranker(
            model = "BAAI/bge-reranker-base",
            top_n = top_k,
        )
        reranked = reranker.postprocess_nodes(nodes, QueryBundle(query))
        final    = [(n.node.text, n.node.metadata, n.score) for n in reranked]

    except Exception:
        # Graceful fallback — use original distance-based order
        final = [
            (doc, meta, round(1 - dist, 3))
            for doc, meta, dist in zip(docs[:top_k], metas[:top_k], dists[:top_k])
        ]

    # ── Format ────────────────────────────────────────────────────
    parts: list[str] = []
    for doc, meta, score in final:
        filename = meta.get("filename", "unknown")
        date     = meta.get("date_added", "")
        snippet  = doc[:800].strip()
        parts.append(
            f"[Source: {filename} | Date: {date} | Relevance: {round(score, 3)}]\n{snippet}"
        )

    return "\n\n---\n\n".join(parts)


# ─── Tool 2: Date-Filtered Search ─────────────────────────────────

def search_notes_by_date(query: str, date_added: str, top_k: int = 4) -> str:
    """
    Search notes restricted to a specific time period (YYYY-MM).

    Args:
        query      : Natural language question or topic.
        date_added : Period filter in YYYY-MM format (e.g. "2024-06").
        top_k      : How many passages to retrieve.

    Returns:
        Formatted string of relevant passages from that period only.
    """
    collection = _get_collection()

    try:
        results = collection.query(
            query_embeddings = [_embed_query(query)],
            n_results        = top_k,
            where            = {"date_added": {"$eq": date_added}},
            include          = ["documents", "metadatas"],
        )
    except Exception as exc:
        return f"Date-filtered search failed: {exc}"

    docs  = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        return f"No notes found for '{query}' in period {date_added}."

    parts: list[str] = []
    for doc, meta in zip(docs, metas):
        filename = meta.get("filename", "unknown")
        snippet  = doc[:800].strip()
        parts.append(f"[{filename} | {date_added}]\n{snippet}")

    return "\n\n---\n\n".join(parts)


# ─── Tool 3: Find Contradictions ──────────────────────────────────

def find_contradictions(topic: str, period_a: str, period_b: str) -> str:
    """
    Compare what your notes say about a topic across two time periods
    and surface intellectual contradictions or shifts in thinking.

    Args:
        topic    : The concept to compare (e.g. "RAG accuracy", "AI ethics").
        period_a : Earlier time period in YYYY-MM format (e.g. "2024-03").
        period_b : Later  time period in YYYY-MM format (e.g. "2025-03").

    Returns:
        A structured analysis of agreements, shifts, and conflicts.
    """
    notes_a = search_notes_by_date(topic, period_a, top_k=4)
    notes_b = search_notes_by_date(topic, period_b, top_k=4)

    if notes_a.startswith("No notes found"):
        return f"⚠ {notes_a} — try a different period or broader topic."
    if notes_b.startswith("No notes found"):
        return f"⚠ {notes_b} — try a different period or broader topic."

    analysis_prompt = CONTRADICT_SYNTHESIS_PROMPT.format(
        query    = f"How has my thinking about '{topic}' changed?",
        period_a = period_a,
        notes_a  = notes_a,
        period_b = period_b,
        notes_b  = notes_b,
    )
    return analysis_prompt


# ─── Tool 4: List Available Periods ───────────────────────────────

def list_available_periods() -> str:
    """
    List all time periods (YYYY-MM) present in the note library.

    Returns:
        JSON string with a list of {period, chunk_count} objects.
    """
    collection = _get_collection()
    try:
        all_meta = collection.get(include=["metadatas"])["metadatas"]
        period_counts: dict[str, int] = {}
        for meta in all_meta:
            period = meta.get("date_added", "unknown")
            period_counts[period] = period_counts.get(period, 0) + 1

        result = sorted(
            [{"period": k, "chunk_count": v} for k, v in period_counts.items()],
            key=lambda x: x["period"],
        )
        return json.dumps(result, indent=2)
    except Exception as exc:
        return f"Could not retrieve periods: {exc}"


# ─── Tool 5: List Topics ──────────────────────────────────────────

def list_topics() -> str:
    """
    List all topic tags present in the indexed notes.

    Returns:
        JSON string with unique topic tags and their document counts.
    """
    collection = _get_collection()
    try:
        all_meta = collection.get(include=["metadatas"])["metadatas"]
        topic_counts: dict[str, int] = {}
        for meta in all_meta:
            topics_str = meta.get("topics", "")
            for t in topics_str.split(","):
                t = t.strip()
                if t:
                    topic_counts[t] = topic_counts.get(t, 0) + 1

        result = sorted(
            [{"topic": k, "chunk_count": v} for k, v in topic_counts.items()],
            key=lambda x: -x["chunk_count"],
        )
        return json.dumps(result, indent=2)
    except Exception as exc:
        return f"Could not retrieve topics: {exc}"


# ─── LlamaIndex Tool Wrappers ─────────────────────────────────────

def get_all_tools() -> list[FunctionTool]:
    """Return all tools wrapped for use by a LlamaIndex agent."""
    return [
        FunctionTool.from_defaults(
            fn          = search_notes,
            name        = "search_notes",
            description = (
                "Search the personal PDF note library for passages relevant to a query. "
                "Use this for direct factual lookups or broad topic exploration."
            ),
        ),
        FunctionTool.from_defaults(
            fn          = search_notes_by_date,
            name        = "search_notes_by_date",
            description = (
                "Search notes filtered to a specific time period (YYYY-MM). "
                "Use when the query specifies 'last month', 'in 2024', etc."
            ),
        ),
        FunctionTool.from_defaults(
            fn          = find_contradictions,
            name        = "find_contradictions",
            description = (
                "Compare what the notes say about a topic across two time periods. "
                "Use when the query asks about changes in thinking, contradictions, "
                "or how understanding of a topic has evolved."
            ),
        ),
        FunctionTool.from_defaults(
            fn          = list_available_periods,
            name        = "list_available_periods",
            description = (
                "List all YYYY-MM time periods present in the note library. "
                "Use this to discover what time periods are available before "
                "calling find_contradictions."
            ),
        ),
        FunctionTool.from_defaults(
            fn          = list_topics,
            name        = "list_topics",
            description = (
                "List all topic tags in the note library with document counts. "
                "Use when the user asks what subjects are covered, or to orient "
                "before a deep search."
            ),
        ),
    ]