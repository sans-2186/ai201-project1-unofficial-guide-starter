"""
Milestone 3 — Document ingestion and chunking for "The Unofficial Guide".

Pipeline: load documents/*.txt  ->  clean  ->  chunk  ->  inspect.

Chunking strategy (see planning.md):
  - ~600 character chunks, ~50 character overlap.
  - Boundary-aware: each top-level comment (plus its nested replies) stays in
    one chunk so a single chunk holds roughly one person's advice. The schedule
    + post form a separate "context" chunk. Only blocks longer than the chunk
    size are sub-split with character overlap.
  - A short "Context: <major>, <semester>" tag is prepended to every chunk so
    the embedder can tell otherwise-identical "Rate my Schedule" threads apart
    (Anticipated Challenge #2 in planning.md).

Each chunk carries metadata (source filename, major, semester, section) so
retrieved results can be attributed back to the thread they came from.

Run directly to inspect the output:
    python ingest.py
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "documents"
CHUNK_SIZE = 600      # characters, per planning.md
CHUNK_OVERLAP = 50    # characters, per planning.md

HEADER_KEYS = ("SOURCE", "URL", "MAJOR", "CLASSIFICATION", "SEMESTER")


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #
def load_documents(docs_dir: Path = DOCS_DIR) -> list[tuple[str, str]]:
    """Read every .txt file from disk. Returns (filename, raw_text) pairs."""
    files = sorted(docs_dir.glob("*.txt"))
    if not files:
        raise FileNotFoundError(f"No .txt files found in {docs_dir}")
    return [(f.name, f.read_text(encoding="utf-8")) for f in files]


# --------------------------------------------------------------------------- #
# Clean
# --------------------------------------------------------------------------- #
def clean_text(text: str) -> str:
    """Normalize the light noise that survives manual copy-paste.

    The documents are already hand-cleaned (no nav/votes/ads), so this only
    normalizes curly quotes/dashes and collapses redundant whitespace.
    """
    replacements = {
        "’": "'", "‘": "'",      # curly single quotes
        "“": '"', "”": '"',      # curly double quotes
        "–": "-", "—": "-",      # en / em dash
        " ": " ",                      # non-breaking space
        "&amp;": "&", "&#39;": "'", "&nbsp;": " ",  # stray HTML entities
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    # collapse runs of spaces/tabs but keep newlines (they carry structure)
    text = re.sub(r"[ \t]+", " ", text)
    return text


# --------------------------------------------------------------------------- #
# Parse into sections
# --------------------------------------------------------------------------- #
def parse_document(filename: str, raw: str) -> dict:
    """Split a document into its header metadata + SCHEDULE / POST / COMMENTS."""
    text = clean_text(raw)

    meta = {"source": filename}
    for key in HEADER_KEYS:
        m = re.search(rf"^{key}:\s*(.+)$", text, flags=re.MULTILINE)
        if m:
            meta[key.lower()] = m.group(1).strip()

    def section(name: str, nexts: tuple[str, ...]) -> str:
        stop = "|".join(nexts)
        pattern = rf"^{name}:\s*\n(.*?)(?=^(?:{stop}):|\Z)" if stop else rf"^{name}:\s*\n(.*)\Z"
        m = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
        return m.group(1).strip() if m else ""

    schedule = section("SCHEDULE", ("POST", "COMMENTS"))
    post = section("POST", ("COMMENTS",))
    comments = section("COMMENTS", ())

    return {"meta": meta, "schedule": schedule, "post": post, "comments": comments}


# --------------------------------------------------------------------------- #
# Chunk
# --------------------------------------------------------------------------- #
def split_with_overlap(text: str, size: int = CHUNK_SIZE,
                       overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split an over-long block into <=size pieces, breaking on whitespace."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []

    chunks, start = [], 0
    while start < len(text):
        end = start + size
        if end < len(text):
            ws = text.rfind(" ", start, end)
            if ws > start:
                end = ws
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, 0)
    return chunks


def _strip_bullets(block: str) -> str:
    """Turn the '- '/indented comment markup into clean readable lines."""
    lines = []
    for line in block.splitlines():
        line = re.sub(r"^\s*-\s+", "", line)   # drop leading "- "
        line = line.strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def split_comment_blocks(comments: str) -> list[str]:
    """Each top-level comment + its nested replies = one block (split on blanks)."""
    raw_blocks = re.split(r"\n\s*\n", comments)
    return [_strip_bullets(b) for b in raw_blocks if _strip_bullets(b)]


def chunk_document(parsed: dict) -> list[Chunk]:
    meta = parsed["meta"]
    major = meta.get("major", "")
    semester = meta.get("semester", "")
    context = f"Context: {major}".strip(", ")
    if semester:
        context += f", {semester}"
    prefix = context + ".\n"

    def make(body: str, section: str) -> list[Chunk]:
        out = []
        for piece in split_with_overlap(body, CHUNK_SIZE - len(prefix)):
            out.append(Chunk(
                text=prefix + piece,
                metadata={**meta, "section": section},
            ))
        return out

    chunks: list[Chunk] = []

    # one "context" chunk: schedule + post (who is asking + their classes)
    head_parts = []
    if parsed["schedule"]:
        head_parts.append("SCHEDULE:\n" + parsed["schedule"])
    if parsed["post"]:
        head_parts.append("POST:\n" + parsed["post"])
    if head_parts:
        chunks += make("\n\n".join(head_parts), "context")

    # one chunk per comment thread
    for block in split_comment_blocks(parsed["comments"]):
        chunks += make(block, "comment")

    # safety: drop any empties
    return [c for c in chunks if c.text.strip()]


def build_chunks(docs_dir: Path = DOCS_DIR) -> list[Chunk]:
    """Full pipeline entry point — used here and by Milestone 4 (embedding)."""
    chunks = []
    for filename, raw in load_documents(docs_dir):
        chunks += chunk_document(parse_document(filename, raw))
    return chunks


# --------------------------------------------------------------------------- #
# Inspect (Milestone 3 checkpoint)
# --------------------------------------------------------------------------- #
def main() -> None:
    chunks = build_chunks()
    n = len(chunks)
    lengths = [len(c.text) for c in chunks]

    print("=" * 70)
    print(f"Loaded chunks: {n}")
    print(f"Chunk length  -> min {min(lengths)} | "
          f"avg {sum(lengths) // n} | max {max(lengths)} chars")

    per_file: dict[str, int] = {}
    for c in chunks:
        per_file[c.metadata["source"]] = per_file.get(c.metadata["source"], 0) + 1
    print("\nChunks per document:")
    for src in sorted(per_file):
        print(f"  {src:<45} {per_file[src]}")

    # sanity bounds from the milestone (50–2000 across the corpus)
    if n < 50:
        print("\n[!] Fewer than 50 chunks — chunks may be too large.")
    elif n > 2000:
        print("\n[!] More than 2000 chunks — chunks may be too small.")
    else:
        print(f"\n[ok] {n} chunks is within the healthy 50–2000 range.")

    if any(not c.text.strip() for c in chunks):
        print("[!] Found empty chunk(s).")

    print("\n" + "=" * 70)
    print("5 random chunks for inspection:")
    for i, c in enumerate(random.sample(chunks, min(5, n)), 1):
        print(f"\n--- chunk {i}  [{c.metadata['source']} | "
              f"{c.metadata.get('section')}]  ({len(c.text)} chars) ---")
        print(c.text)


if __name__ == "__main__":
    main()
