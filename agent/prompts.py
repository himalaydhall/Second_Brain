# ─────────────────────────────────────────────────────────────────
#  agent/prompts.py
#  All prompts in one place so you can tweak behaviour without
#  hunting through agent logic.
# ─────────────────────────────────────────────────────────────────

# ── Query Classifier ──────────────────────────────────────────────
CLASSIFY_PROMPT = """\
You are routing an incoming query to the right search mode.

Classify the query into EXACTLY ONE of:
  - simple      : a direct factual lookup ("What does X say about Y?")
  - compare     : needs to synthesise multiple sources ("What are the main themes in my AI notes?")
  - contradict  : explicitly asks for conflicts, shifts in thinking, or contradictions across time

Query: {query}

Reply with ONLY the single mode word. No explanation."""


# ── Simple Synthesis ──────────────────────────────────────────────
SIMPLE_SYNTHESIS_PROMPT = """\
You are a research assistant surfacing insights from a personal note library.

The user asked: "{query}"

Here are the most relevant passages retrieved from their PDFs:

{context}

Provide a clear, concise answer grounded in the retrieved text.
ALWAYS cite the source filename in square brackets for every fact (e.g. [AStar_Example.pdf]).
If the retrieved text does not answer the question, say so clearly — do not guess."""

COMPARE_SYNTHESIS_PROMPT = """\
You are a research assistant synthesising insights across multiple PDFs in a personal library.

The user asked: "{query}"

Retrieved passages (from multiple documents):

{context}

Respond with:
1. A markdown table with EXACTLY 3 columns: Aspect | Topic A | Topic B.
   - Identify the TWO main topics or concepts being compared from the query.
   - Use those topic names as column headers, NOT filenames.
   - Rows: Approach, Strengths, Weaknesses, Best Used For, Key Idea.
   - Keep each cell to ONE short phrase (max 8 words).
   - Use "—" if a topic has no information for that aspect.
2. A single sentence summarising the most important difference.

Do NOT use filenames as column headers.
Do NOT create more than 3 columns.
Do NOT write paragraphs."""


# ── Contradiction Analysis ────────────────────────────────────────
CONTRADICT_SYNTHESIS_PROMPT = """\
You are an intellectual mirror — helping a researcher see how their thinking has evolved.

The user asked: "{query}"

Notes from PERIOD A ({period_a}):
{notes_a}

Notes from PERIOD B ({period_b}):
{notes_b}

Analyse these notes and produce:

1. AGREEMENTS  — What do both periods say consistently?
2. SHIFTS      — Where has the thinking changed? Quote specific phrases from each period.
3. CONFLICTS   — Are there direct contradictions? Be precise about which documents conflict.
4. OPEN QUESTION — What single question would help the user resolve the most important tension?

Format with clear headers. Cite source filenames."""


# ── Human-in-the-Loop Clarification ──────────────────────────────
HITL_CLARIFY_PROMPT = """\
You found conflicting or ambiguous information in the user's notes.

Conflicting passages:
{conflict_summary}

Write ONE short, specific question to ask the user that would help you give a better answer.
The question should resolve the most important ambiguity.
Ask ONLY one question. Keep it under 30 words."""


# ── Sub-question Decomposition ────────────────────────────────────
SUB_QUESTION_SYSTEM_PROMPT = """\
You are a research planning assistant.
Break complex queries into specific, atomic sub-questions that can each be answered
by searching a single topic in a note library.
Return ONLY a JSON array of sub-question strings.
Example: ["What does note A say about X?", "What does note B say about Y?"]"""
