# ─────────────────────────────────────────────────────────────────
#  config.py  –  Central configuration loader
#  All settings flow from .env → here → everywhere else.
# ─────────────────────────────────────────────────────────────────

import os
import functools
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────
NOTES_FOLDER   = Path(os.getenv("NOTES_FOLDER",   "./data/your_notes_folder"))
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "./data/chroma_db"))
MANIFEST_PATH  = Path(os.getenv("MANIFEST_PATH",  "./data/manifest.json"))

CHROMA_COLLECTION_NAME = "pdf_notes"

# ── LLM ───────────────────────────────────────────────────────────
LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3.2")

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL",   "gemini-2.0-flash")

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")

# ── Embeddings ────────────────────────────────────────────────────
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local").lower()
# Local model: free, runs offline, good quality for semantic search
LOCAL_EMBED_MODEL = "BAAI/bge-base-en-v1.5" 

# ── LlamaParse ────────────────────────────────────────────────────
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")

# ── Agent behaviour ───────────────────────────────────────────────
TOP_K_SIMPLE   = 5  # results to fetch for simple queries=3(Previous)
TOP_K_COMPLEX  = 5   # results to fetch for compare / contradict queries=6(Previous)
TIMEOUT_SECS   = 120 # max seconds before a workflow step times out


def get_llm():
    """Return a LlamaIndex LLM instance based on .env settings."""
    if LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")
        from llama_index.llms.gemini import Gemini
        return Gemini(
            api_key=GEMINI_API_KEY,
            model_name=f"models/{GEMINI_MODEL}",
    )
    elif LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")
        from llama_index.llms.openai import OpenAI
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        return OpenAI(model="gpt-4o-mini")

    elif LLM_PROVIDER == "groq":
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY is not set.")
        from llama_index.llms.groq import Groq
        return Groq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=os.getenv("GROQ_API_KEY"),
            timeout=TIMEOUT_SECS,    # ← only this line added
    )
    else:  # default: ollama
        from llama_index.llms.ollama import Ollama
        return Ollama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            request_timeout=TIMEOUT_SECS,
            context_window=4096,
        )



@functools.lru_cache(maxsize=1)
def get_embed_model():
    """Return a LlamaIndex embedding model based on .env settings."""
    if EMBEDDING_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is needed for Gemini embeddings.")
        from llama_index.embeddings.gemini import GeminiEmbedding
        return GeminiEmbedding(api_key=GEMINI_API_KEY)

    else:  # default: local HuggingFace
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        return HuggingFaceEmbedding(model_name=LOCAL_EMBED_MODEL)
