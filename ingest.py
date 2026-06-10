"""
Milestone 3 — Document ingestion and chunking for "The Unofficial Guide".

Pipeline: load documents/*.txt  ->  chunk  ->  inspect.

Adapted from the course starter scaffold: a character-based sliding window
with overlap, returning a flat list of chunk dicts. Chunk size/overlap come
from planning.md (600 / 50). Each chunk keeps the source filename so a
retrieved result can be traced back to the thread it came from.

Run directly to inspect the output (the Milestone 3 checkpoint):
    python ingest.py
"""

import os
import random
import re

from config import DOCS_PATH, CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_LENGTH


def load_documents():
    """Load all .txt source documents from the documents folder."""
    documents = []
    for filename in sorted(os.listdir(DOCS_PATH)):
        if filename.endswith(".txt"):
            filepath = os.path.join(DOCS_PATH, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            source = filename.replace(".txt", "")
            documents.append({
                "source": source,
                "filename": filename,
                "text": text,
            })
    print(f"Loaded {len(documents)} document(s): {[d['source'] for d in documents]}")
    return documents


def _window(text):
    """Character sliding window with overlap, for a block longer than CHUNK_SIZE.

    Breaks on the nearest whitespace before the size limit so pieces don't start
    or end mid-word.
    """
    pieces = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        # Step back by `overlap`, then snap forward to the next space so the
        # next piece also starts on a word boundary (keeps most of the overlap).
        new_start = max(end - CHUNK_OVERLAP, start + 1)
        space = text.find(" ", new_start)
        if space != -1 and space < end:
            new_start = space + 1
        start = new_start
    return pieces


def chunk_document(text, source):
    """
    Split a source document into chunks ready for embedding.

    Strategy: boundary-aware, then sliding window only where needed.
      - First split the document on blank lines, so each block is a natural
        unit: the header, the schedule, the post, and one block per comment
        (a comment plus its nested replies stays together). This keeps a chunk
        to roughly one person's advice instead of cutting mid-sentence.
      - chunk_size = 600 characters (~150 tokens): only blocks longer than this
        (a few very long comments) get split further with a sliding window.
      - overlap = 50 characters: duplicates a small window at each boundary so
        advice split across two pieces can still be retrieved intact.
      - min_length = 50 characters: filters whitespace artifacts and very short
        fragments that add noise without useful meaning.

    Returns a list of dicts, each with:
      - "text"     : the chunk text (str)
      - "source"   : the source filename stem, e.g. "01_science_lastminute"
      - "chunk_id" : a unique id, e.g. "01_science_lastminute_0"
    """
    chunks = []
    counter = 0

    # one block per blank-line-separated section / comment thread
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue

        # keep short blocks whole; only window the long ones
        pieces = [block] if len(block) <= CHUNK_SIZE else _window(block)

        for piece in pieces:
            if len(piece) >= MIN_CHUNK_LENGTH:
                chunks.append({
                    "text": piece,
                    "source": source,
                    "chunk_id": f"{source}_{counter}",
                })
                counter += 1

    return chunks


def build_chunks():
    """Full pipeline entry point — used here and by Milestone 4 (embedding)."""
    chunks = []
    for doc in load_documents():
        chunks.extend(chunk_document(doc["text"], doc["source"]))
    return chunks


def main():
    """Milestone 3 checkpoint: counts, length stats, and 5 random chunks."""
    chunks = build_chunks()
    n = len(chunks)
    lengths = [len(c["text"]) for c in chunks]

    print("=" * 70)
    print(f"Total chunks: {n}")
    print(f"Chunk length -> min {min(lengths)} | "
          f"avg {sum(lengths) // n} | max {max(lengths)} chars")

    per_source = {}
    for c in chunks:
        per_source[c["source"]] = per_source.get(c["source"], 0) + 1
    print("\nChunks per document:")
    for src in sorted(per_source):
        print(f"  {src:<42} {per_source[src]}")

    # sanity bounds from the milestone (50-2000 across the corpus)
    if n < 50:
        print("\n[!] Fewer than 50 chunks — chunks may be too large.")
    elif n > 2000:
        print("\n[!] More than 2000 chunks — chunks may be too small.")
    else:
        print(f"\n[ok] {n} chunks is within the healthy 50-2000 range.")

    if any(not c["text"].strip() for c in chunks):
        print("[!] Found empty chunk(s).")

    print("\n" + "=" * 70)
    print("5 random chunks for inspection:")
    for i, c in enumerate(random.sample(chunks, min(5, n)), 1):
        print(f"\n--- chunk {i}  [{c['chunk_id']}]  ({len(c['text'])} chars) ---")
        print(c["text"])


if __name__ == "__main__":
    main()
