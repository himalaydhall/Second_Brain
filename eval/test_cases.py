# ─────────────────────────────────────────────────────────────────
#  eval/test_cases.py
#
#  Define your ground-truth test cases here.
#  These are questions where YOU know the correct answer from
#  your own PDFs. Run eval/run_eval.py to score the agent.
#
#  ─── HOW TO WRITE GOOD TEST CASES ──────────────────────────────
#
#  1. Pick questions with concrete, verifiable answers in your PDFs.
#  2. expected_keywords: 3-6 words/phrases that MUST appear in a
#     correct answer. Keep them specific, not generic.
#  3. expected_source: filename that should be cited (or None if
#     the answer spans multiple docs).
#  4. mode: "simple" | "compare" | "contradict"
#
#  ─── EXAMPLE CASES (replace with your own) ────────────────────
# ─────────────────────────────────────────────────────────────────

TEST_CASES = [
    
    {
        "id"                : "simple_001",
        "mode"              : "simple",
        "query"             : "What is the fitness function used in the 4-Queen genetic algorithm?",
        "expected_keywords" : ["fitness", "conflicts", "chromosome"],
        "expected_source"   : None,
        "notes"             : "Answer is F(C) = 1 / (1 + Conflicts(C))",
    },
    {
        "id"                : "simple_002",
        "mode"              : "simple",
        "query"             : "What are the two values maintained in Alpha-Beta pruning?",
        "expected_keywords" : ["alpha", "beta"],
        "expected_source"   : None,
        "notes"             : "Clear answer in adversarial search PDF",
    },
    {
        "id"                : "simple_003",
        "mode"              : "simple",
        "query"             : "What is the formula for f(n) in A* search?",
        "expected_keywords" : ["f", "start", "goal"],
        "expected_source"   : None,
        "notes"             : "f(n) = g(n) + h(n)",
    },
    {
        "id"                : "simple_004",
        "mode"              : "simple",
        "query"             : "What crossover methods are used in the 4-Queen genetic algorithm?",
        "expected_keywords" : ["crossover", "pmx", "order"],
        "expected_source"   : None,
        "notes"             : "PMX and Order Crossover (OX) are both described",
    },
    {
        "id"                : "compare_001",
        "mode"              : "compare",
        "query"             : "Compare how A* search and minimax search find optimal solutions",
        "expected_keywords" : ["optimal", "cost", "minimax"],
        "expected_source"   : None,
        "notes"             : "Specific comparison across two PDFs",
    },
    {
        "id"                : "compare_002",
        "mode"              : "compare",
        "query"             : "What roles do selection and fitness play in genetic algorithms?",
        "expected_keywords" : ["selection", "fitness", "chromosome"],
        "expected_source"   : None,
        "notes"             : "Focused on GA PDF",
    },

    # ── Contradiction detection ───────────────────────────────────
#    {
#        "id"                : "contradict_001",
#        "mode"              : "contradict",
#        "query"             : "How has the view on LLM reliability changed in my notes over time?",
#        "expected_keywords" : ["hallucination", "reliability", "improvement", "benchmark"],
#        "expected_source"   : None,
#        "notes"             : "Requires at least two different date periods in the DB",
#    },

    # ── Add your own cases below ──────────────────────────────────
    # {
    #     "id"                : "simple_003",
    #     "mode"              : "simple",
    #     "query"             : "What does my note on X say about Y?",
    #     "expected_keywords" : ["keyword1", "keyword2"],
    #     "expected_source"   : "your_actual_file.pdf",
    #     "notes"             : "I read this in Jan 2025",
    # },
]
