# ─────────────────────────────────────────────────────────────────
#  utils/metadata.py
#  Handles manifest.json — the ground-truth record of every PDF
#  you've added to your Second Brain, with dates and topic tags.
# ─────────────────────────────────────────────────────────────────

from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import config


# ─── Manifest Schema ──────────────────────────────────────────────
# Each entry in manifest.json looks like:
#
# "attention_is_all_you_need.pdf": {
#     "date_added":  "2024-06",          # YYYY-MM  (when YOU read/added it)
#     "topics":      ["transformers", "attention", "nlp"],
#     "source":      "arxiv",            # free-text origin label
#     "notes":       "Foundational paper on self-attention"  # optional
# }
# ─────────────────────────────────────────────────────────────────


def load_manifest() -> dict:
    """Load manifest from disk. Returns empty dict if not found."""
    if config.MANIFEST_PATH.exists():
        with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_manifest(manifest: dict) -> None:
    """Persist manifest to disk."""
    config.MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def get_metadata_for_pdf(pdf_path: str | Path, manifest: dict) -> dict:
    """
    Return the metadata dict for a given PDF.

    Priority order:
      1. Explicit entry in manifest.json (most accurate)
      2. File modification time as fallback for date_added
    """
    name = Path(pdf_path).name
    entry = manifest.get(name, {})

    # Fallback: use file mtime if no manifest entry
    if "date_added" not in entry:
        try:
            mtime = os.stat(str(pdf_path)).st_mtime
            entry["date_added"] = datetime.fromtimestamp(mtime).strftime("%Y-%m")
        except Exception:
            entry["date_added"] = datetime.now().strftime("%Y-%m")

    entry.setdefault("topics", [])
    entry.setdefault("source", "pdf")
    entry.setdefault("notes", "")

    return {
        "filename":   name,
        "file_path":  str(pdf_path),
        "date_added": entry["date_added"],
        "topics":     ",".join(entry["topics"]),   # ChromaDB needs strings
        "source":     entry["source"],
        "notes":      entry["notes"],
    }


def upsert_manifest_entry(
    filename: str,
    date_added: Optional[str] = None,
    topics: Optional[list[str]] = None,
    source: str = "pdf",
    notes: str = "",
) -> None:
    """
    Add or update one PDF entry in the manifest.
    date_added format: "YYYY-MM"
    """
    manifest = load_manifest()
    manifest[filename] = {
        "date_added": date_added or datetime.now().strftime("%Y-%m"),
        "topics":     topics or [],
        "source":     source,
        "notes":      notes,
    }
    save_manifest(manifest)


def list_manifest_entries() -> list[dict]:
    """Return all manifest entries as a list of dicts, sorted by date."""
    manifest = load_manifest()
    rows = []
    for filename, meta in manifest.items():
        rows.append({"filename": filename, **meta})
    return sorted(rows, key=lambda r: r.get("date_added", ""), reverse=True)
