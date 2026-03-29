# 🧠 Second Brain — PDF Insight Surfer

An agentic RAG system that doesn't just *search* your PDFs — it **reasons** across them.
Ask it to compare ideas, find contradictions across time, and synthesise themes from your personal library.

---

## What This Does

| Query type | Example | What the agent does |
|---|---|---|
| **Simple** | "What does my note on transformers say about positional encoding?" | Retrieves top relevant chunks and answers directly |
| **Compare** | "What are the main themes in my AI safety reading?" | Breaks query into sub-questions, searches each, synthesises |
| **Contradict** | "How has my view on LLM reliability changed over the past year?" | Pulls notes from two time periods and surfaces intellectual shifts |

---

## Project Structure

```
second_brain/
├── README.md                   ← You are here
├── requirements.txt
├── .env.example                ← Copy to .env and fill in
├── config.py                   ← Central config (LLM, paths, etc.)
│
├── manifest_builder.py         ← Step 1: Tag your PDFs with dates + topics
├── ingest.py                   ← Step 2: Parse and index PDFs into ChromaDB
│
├── agent/
│   ├── workflow.py             ← The brain: LlamaIndex event-driven Workflow
│   ├── tools.py                ← search_notes, find_contradictions, etc.
│   └── prompts.py              ← All LLM prompts (tweak here to tune behaviour)
│
├── eval/
│   ├── test_cases.py           ← Ground-truth Q&A pairs (edit these!)
│   └── run_eval.py             ← Scorer: tells you if the agent is working
│
├── ui/
│   └── app.py                  ← Streamlit chat interface
│
└── data/
    ├── your_notes_folder/      ← DROP YOUR PDFs HERE
    ├── manifest.json.example   ← Example metadata format
    └── chroma_db/              ← Auto-created by ingest.py
```

---

## Prerequisites

### 1. Python 3.10+

```bash
python --version   # should be 3.10 or higher
```

### 2. Choose your LLM

**Option A — Ollama (free, local, recommended to start)**
```bash
# Install: https://ollama.com
ollama pull llama3.2         # ~2GB download
ollama serve                 # keep this running in a terminal
```

**Option B — Gemini (faster, cloud, free tier available)**
- Get API key at https://aistudio.google.com/app/apikey
- Set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY=...` in `.env`

### 3. (Optional) LlamaParse — for scanned PDFs
- Free tier: 1000 pages/day
- Get key at https://cloud.llamaindex.ai
- Set `LLAMA_CLOUD_API_KEY=...` in `.env`
- If you skip this, scanned PDFs fall back to PyMuPDF (lower quality)

---

## Setup — Step by Step

### Step 1: Clone and install

```bash
cd second_brain
pip install -r requirements.txt
```

### Step 2: Configure

```bash
cp .env.example .env
# Open .env and set your LLM choice and API keys
```

The minimum you need for local setup:
```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
EMBEDDING_PROVIDER=local
```

### Step 3: Add your PDFs

Copy your PDFs into the notes folder:
```bash
cp /path/to/your/papers/*.pdf data/your_notes_folder/
```

Or point to a different folder in `.env`:
```
NOTES_FOLDER=/Users/yourname/Documents/research-papers
```

### Step 4: Build the manifest (recommended)

This is what lets the agent answer "what did I read *last year*?" accurately.

**Interactive mode** (prompts you for each PDF):
```bash
python manifest_builder.py
```

**Auto mode** (uses file modification dates, no prompts):
```bash
python manifest_builder.py --auto
```

Edit `data/manifest.json` directly anytime. See `data/manifest.json.example` for format.

### Step 5: Ingest (index your PDFs)

```bash
python ingest.py
```

This will:
- Classify each PDF (text-native vs scanned)
- Extract text using pdfplumber (text) or LlamaParse (scanned)
- Chunk, embed, and store in ChromaDB
- Skip already-indexed files

To re-index everything from scratch:
```bash
python ingest.py --reset
```

To index a single file:
```bash
python ingest.py --file data/your_notes_folder/paper.pdf
```

### Step 6: Verify with eval

Before you trust the agent, run the test suite:
```bash
```

Edit `eval/test_cases.py` to add questions from your own PDFs. Aim for ≥80% pass rate.

### Step 7: Launch the UI

```bash
streamlit run ui/app.py
```

Opens at http://localhost:8501

---

## How to Use

### Chat interface
Type any question in the chat input. The agent automatically classifies it and picks the right search strategy.

**Simple questions:**
> "What is the difference between RAG and fine-tuning according to my notes?"

**Cross-document questions:**
> "What are the recurring themes in my machine learning papers?"

**Temporal contradiction queries:**
> "How has my view on prompt engineering changed between 2024 and 2025?"
> "What did I believe about AI safety last year that contradicts my recent notes?"

### Human-in-the-Loop (HITL)
Toggle **Human-in-the-Loop** in the sidebar. When on, the agent will pause and ask you a clarifying question when it finds conflicting information before giving its final answer.

---

## Tuning and Customisation

### Change chunk size
In `config.py`:
```python
Settings.chunk_size    = 512   # smaller = more precise retrieval
Settings.chunk_overlap = 64    # overlap prevents cutting ideas mid-sentence
```
After changing: `python ingest.py --reset`

### Change retrieval depth
In `config.py`:
```python
TOP_K_SIMPLE  = 3   # chunks fetched for simple queries
TOP_K_COMPLEX = 6   # chunks fetched for compare/contradict
```

### Tune prompts
All prompts are in `agent/prompts.py`. Edit them without touching agent logic.

### Switch embedding model
In `.env`:
```
EMBEDDING_PROVIDER=local    # free, ~130MB, works offline
EMBEDDING_PROVIDER=gemini   # requires GEMINI_API_KEY
```
**After changing embedding model, always re-ingest:** `python ingest.py --reset`

---

## Roadmap

| Week | Goal |
|---|---|
| 1 | Ingestion working. 10+ PDFs indexed. Eval ≥ 60%. |
| 1.5 | Eval ≥ 80%. Manifest populated with real dates. |
| 2 | Streamlit UI running. Compare + contradict queries working. |
| 2.5 | HITL toggle tested. find_contradictions returning accurate results. |
| 3 | Add more PDFs. Tune chunk size. Share with others. |

---

## Troubleshooting

**`Connection refused` when querying**
→ Ollama is not running. Run `ollama serve` in a separate terminal.

**Empty search results**
→ Run `python ingest.py` first. Check that PDFs are in `data/your_notes_folder/`.

**"No notes found" for a date period**
→ Run `python manifest_builder.py --auto` to populate dates, then `python ingest.py --reset`.

**Scanned PDFs produce garbage text**
→ Set `LLAMA_CLOUD_API_KEY` in `.env` to enable LlamaParse.

**Streamlit shows old results**
→ Clear conversation in the sidebar or restart Streamlit.

**Eval score below 60%**
→ Try a smarter model (Gemini instead of Ollama llama3.2), smaller chunk size, or more topic tags in manifest.

---

## Architecture

```
Your Question
      │
      ▼
┌─────────────────┐
│  classify_query  │  ← LLM decides: simple / compare / contradict
└────────┬────────┘
         │
    ┌────┴─────────────────────┐
    │                          │                      │
 simple                    compare               contradict
    │                          │                      │
search_notes          sub_question_search    contradiction_search
 (top-k)              (decompose → merge)   (period A vs period B)
    │                          │                      │
    └──────────────────────────┴──────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │    maybe_clarify     │  ← HITL (optional)
                    └──────────┬──────────┘
                               │
                         synthesise
                          (LLM call)
                               │
                           Answer ✅
```

---

## Credits

Built with:
- [LlamaIndex](https://www.llamaindex.ai) — agent framework and workflows
- [ChromaDB](https://www.trychroma.com) — local vector store
- [pdfplumber](https://github.com/jsvine/pdfplumber) — text PDF extraction
- [PyMuPDF](https://pymupdf.readthedocs.io) — PDF classification and fast extraction
- [LlamaParse](https://cloud.llamaindex.ai) — scanned PDF parsing (optional)
- [Streamlit](https://streamlit.io) — chat UI
- [Ollama](https://ollama.com) — local LLM runtime
