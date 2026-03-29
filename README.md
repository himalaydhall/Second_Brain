# 🧠 Second Brain — PDF Insight Surfer

An agentic RAG system that doesn't just *search* your PDFs — it **reasons** across them.
Ask it to compare ideas, find contradictions across time, and synthesise themes from your personal library.

---

## What This Does

| Query type | Example | What the agent does |
|---|---|---|
| **Simple** | "What is alpha-beta pruning?" | Retrieves top relevant chunks and answers directly |
| **Compare** | "What are the main themes across my AI notes?" | Breaks query into sub-questions, searches each, synthesises |
| **Contradict** | "How has my view on LLM reliability changed over the past year?" | Pulls notes from two time periods and surfaces intellectual shifts |

---

## Technical Stack

| Component | Choice | Why |
|---|---|---|
| LLM | Groq (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) | Free tier, ~500 tok/s, no local GPU needed |
| Embeddings | HuggingFace `BAAI/bge-small-en-v1.5` | Free, offline, ~130MB, good semantic quality |
| Vector DB | ChromaDB (local, persistent) | Zero-config, no server needed |
| PDF parsing | pdfplumber + PyMuPDF + LlamaParse (scanned, optional) | Free for text-native PDFs |
| UI | Streamlit | Streaming responses, minimal setup |

**Routing logic:** Simple queries use `llama-3.1-8b-instant` (~2-3s). Compare and contradict queries use `llama-3.3-70b-versatile` for better reasoning.

---

## Project Structure

```
second_brain/
├── README.md
├── requirements.txt
├── .env.example                ← Copy to .env and fill in your keys
├── config.py                   ← Central config (LLM, paths, settings)
│
├── quick_start.py              ← Verify your setup before ingesting
├── manifest_builder.py         ← Tag your PDFs with dates and topics
├── ingest.py                   ← Parse and index PDFs into ChromaDB
│
├── agent/
│   ├── workflow.py             ← Reasoning pipeline (classify → search → synthesise)
│   ├── tools.py                ← search_notes, find_contradictions, list_topics, etc.
│   └── prompts.py              ← All LLM prompts (tune here to change behaviour)
│
├── eval/
│   ├── test_cases.py           ← Ground-truth Q&A pairs (edit for your PDFs)
│   └── run_eval.py             ← Scores the agent before you trust it
│
├── ui/
│   └── app.py                  ← Streamlit chat interface with streaming
│
└── data/
    ├── your_notes_folder/      ← DROP YOUR PDFs HERE
    ├── manifest.json.example   ← Example metadata format
    └── chroma_db/              ← Auto-created by ingest.py
```

---

## Setup

### Prerequisites

- Python 3.10+
- A free [Groq API key](https://console.groq.com/keys) (no credit card needed)
- *(Optional)* A free [LlamaCloud key](https://cloud.llamaindex.ai) for scanned PDFs

### Step 1 — Install

```bash
git clone https://github.com/himalaydhall/Second_Brain.git
cd Second_Brain
pip install -r requirements.txt
```

### Step 2 — Configure

```bash
cp .env.example .env
```

Minimum required settings in `.env`:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_PROVIDER=local
```

*(Optional)* Add `LLAMA_CLOUD_API_KEY` for LlamaParse (scanned/complex PDFs). Without it, scanned PDFs fall back to PyMuPDF.

### Step 3 — Verify setup

```bash
python quick_start.py
```

Checks all dependencies, confirms API connectivity, and tells you exactly what's missing.

### Step 4 — Add your PDFs

```bash
cp /path/to/your/papers/*.pdf data/your_notes_folder/
```

Or set a custom folder in `.env`:
```env
NOTES_FOLDER=/Users/yourname/Documents/research-papers
```

### Step 5 — Build the manifest

The manifest gives the agent temporal awareness — it's what makes "what did I read *last month*?" work accurately.

```bash
# Auto mode — uses file modification dates, no prompts
python manifest_builder.py --auto

# Interactive mode — prompts you for date + topic tags per PDF
python manifest_builder.py
```

Edit `data/manifest.json` anytime to improve tags. See `data/manifest.json.example` for the format.

### Step 6 — Index your PDFs

```bash
python ingest.py
```

Classifies each PDF, extracts text, chunks, embeds, and stores in ChromaDB. Already-indexed files are skipped.

```bash
python ingest.py --reset          # wipe DB and re-index everything
python ingest.py --file paper.pdf # index a single file
```

### Step 7 — Verify the agent works

```bash
python -m eval.run_eval
```

Edit `eval/test_cases.py` with questions from your actual PDFs. Aim for ≥80% before trusting the UI.

### Step 8 — Launch

```bash
streamlit run ui/app.py
```

Opens at **http://localhost:8501**

---

## How to Use

The agent automatically classifies every query — you don't need to specify the mode.

**Simple lookup:**
```
What is the fitness function in a genetic algorithm?
What does alpha-beta pruning do?
```

**Cross-document synthesis:**
```
Compare how A* and minimax search find optimal solutions
What are the main AI search algorithms covered in my notes?
```

**Temporal contradiction:**
```
How has my understanding of RAG changed between 2024 and 2025?
What did I believe about AI safety last year that contradicts my recent notes?
```

### Adding more PDFs over time

```bash
python manifest_builder.py --auto   # update manifest
python ingest.py                    # index new files (skips existing)
```

### Human-in-the-Loop (HITL)

Toggle **Human-in-the-Loop** in the sidebar. The agent will pause and ask you a clarifying question when it finds conflicting information before giving its final answer.

---

## Configuration Reference

| Setting | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq` / `ollama` / `gemini` / `openai` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model for compare/contradict queries |
| `EMBEDDING_PROVIDER` | `local` | `local` (free) or `gemini` |
| `TOP_K_SIMPLE` | `5` | Chunks retrieved for simple queries |
| `TOP_K_COMPLEX` | `5` | Chunks retrieved for compare/contradict |
| `NOTES_FOLDER` | `./data/your_notes_folder` | Where your PDFs live |
| `CHROMA_DB_PATH` | `./data/chroma_db` | Where the vector DB is stored |

> After changing `EMBEDDING_PROVIDER` or chunk settings, always re-ingest: `python ingest.py --reset`

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Empty search results | Run `python ingest.py`. Confirm PDFs are in `data/your_notes_folder/` |
| "No notes found" for a date period | Run `python manifest_builder.py --auto` then `python ingest.py --reset` |
| Groq rate limit (429) | Wait 60s or switch to `llama-3.1-8b-instant` in `.env` |
| Scanned PDFs garbled | Add `LLAMA_CLOUD_API_KEY` to `.env` |
| Eval score below 60% | Reduce `TOP_K` to stay under token limits, or add topic tags in `manifest.json` |
| Ollama out-of-memory | Add `context_window=4096` to `get_llm()` in `config.py` |

---

## Architecture

```
Your Question
      │
      ▼
┌─────────────────┐
│  classify_query  │  ← Fast 8b model: simple / compare / contradict
└────────┬────────┘
         │
    ┌────┴──────────────────────────┐
    │                               │                         │
 simple                         compare                  contradict
    │                               │                         │
search_notes                sub_question_search      contradiction_search
(top-k chunks)              (decompose → merge)      (period A vs period B)
    │                               │                         │
    └───────────────────────────────┴─────────────────────────┘
                                    │
                         ┌──────────┴──────────┐
                         │    maybe_clarify     │  ← HITL (optional)
                         └──────────┬──────────┘
                                    │
                              synthesise
                         (70b model, streaming)
                                    │
                                Answer ✅
```

---

## Credits

- [LlamaIndex](https://www.llamaindex.ai) — agent tooling and embeddings
- [Groq](https://groq.com) — fast LLM inference
- [ChromaDB](https://www.trychroma.com) — local vector store
- [pdfplumber](https://github.com/jsvine/pdfplumber) — text PDF extraction
- [PyMuPDF](https://pymupdf.readthedocs.io) — PDF classification and fast text extraction
- [LlamaParse](https://cloud.llamaindex.ai) — scanned PDF parsing (optional)
- [Streamlit](https://streamlit.io) — chat UI
