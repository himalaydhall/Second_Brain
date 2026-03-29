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

## Technical Specifications

This repository is currently configured for maximum speed and efficient local embedding:
*   **LLM Provider:** Groq Engine (`llama-3.3-70b-versatile`) for extremely fast reasoning and parsing.
*   **Embedding Provider:** Local HuggingFace (`BAAI/bge-base-en-v1.5`) for free, offline, high-quality vector embeddings.
*   **Vector Database:** Local ChromaDB
*   **Vector Search Scope:** `TOP_K_SIMPLE = 5`, `TOP_K_COMPLEX = 5`

---

## Project Structure

```text
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
│   ├── workflow.py             ← LlamaIndex event-driven Workflow routing
│   ├── tools.py                ← search_notes, find_contradictions, etc.
│   └── prompts.py              ← All LLM prompts
│
├── eval/
│   ├── test_cases.py           ← Ground-truth Q&A pairs
│   └── run_eval.py             ← Scorer evaluating the agent
│
├── ui/
│   └── app.py                  ← Streamlit chat interface
│
└── data/
    ├── your_notes_folder/      ← DROP YOUR PDFs HERE
    ├── manifest.json           ← Active metadata file
    └── chroma_db/              ← Auto-created by ingest.py
```

---

## Setup — Step by Step

### Step 1: Clone and install

```bash
git clone https://github.com/himalaydhall/Second_Brain.git
cd Second_Brain
pip install -r requirements.txt
```

### Step 2: Configure Environment

Copy the example file to create your active `.env`:
```bash
cp .env.example .env
```

Open `.env` and set your Groq API key (get one [here](https://console.groq.com/keys)):
```env
# Minimum required setup
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_PROVIDER=local
```
*(Optional)* Add a LlamaCloud API key to `LLAMA_CLOUD_API_KEY` to enable LlamaParse for scanned/complex PDFs.

### Step 3: Add your PDFs

Copy your PDFs into the notes folder:
```bash
cp /path/to/your/papers/*.pdf data/your_notes_folder/
```

### Step 4: Build the metadata manifest

This gives the agent temporal awareness ("what did I read *last year*?"):
```bash
# Auto mode (extracts dates from file metadata)
python manifest_builder.py --auto
```

### Step 5: Ingest (index your PDFs)

```bash
python ingest.py
```
This extracts text, chunks it, generates `BAAI/bge-base-en-v1.5` embeddings, and stores them in ChromaDB. *(To completely rebuild the database later, run `python ingest.py --reset`)*.

### Step 6: Launch the UI

```bash
streamlit run ui/app.py
```
Open your browser at **http://localhost:8501** to start chatting.

---

## How to Use

### Chat interface
Type any question. The Groq-powered workflow automatically classifies the query and runs the appropriate LlamaIndex strategy:

*   **Simple questions:** "What is the difference between RAG and fine-tuning?"
*   **Cross-document questions:** "What are the recurring themes in my ML papers?"
*   **Temporal contradiction:** "What did I believe about AI safety last year that contradicts my recent notes?"

### Human-in-the-Loop (HITL)
Toggle **Human-in-the-Loop** in the sidebar. When active, the agent will pause and request clarification via the Streamlit UI if it finds conflicting information before delivering a final synthesis.

---

## Troubleshooting

*   **Empty search results:** Run `python ingest.py` first and ensure PDFs are inside `data/your_notes_folder/`.
*   **"No notes found" for a date period:** Run `python manifest_builder.py --auto` to log dates, then re-index with `python ingest.py --reset`.
*   **Groq timeout / Rate Limit Error:** Check `.env` for `GROQ_API_KEY` validity or lower your prompt intensity.

---

## Credits
*   [LlamaIndex](https://www.llamaindex.ai) — Workflows & routing
*   [Groq](https://groq.com/) — Lightning-fast LLM Inference
*   [ChromaDB](https://www.trychroma.com) — Local Vector Database
*   [Streamlit](https://streamlit.io) — Chat Interface
