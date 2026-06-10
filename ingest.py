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


HEADER_KEYS = ("SOURCE", "URL", "MAJOR", "CLASSIFICATION", "SEMESTER")


def parse_document(text):
    """Pull the header fields and the SCHEDULE / POST / COMMENTS sections apart."""
    meta = {}
    for key in HEADER_KEYS:
        m = re.search(rf"^{key}:\s*(.+)$", text, flags=re.MULTILINE)
        meta[key.lower()] = m.group(1).strip() if m else ""

    def section(name, nexts):
        stop = "|".join(nexts)
        pattern = (rf"^{name}:\s*\n(.*?)(?=^(?:{stop}):|\Z)" if stop
                   else rf"^{name}:\s*\n(.*)\Z")
        m = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
        return m.group(1).strip() if m else ""

    schedule = section("SCHEDULE", ("POST", "COMMENTS"))
    post = section("POST", ("COMMENTS",))
    comments = section("COMMENTS", ())
    return meta, schedule, post, comments


def _window(text):
    """Word-boundary sliding window — fallback for a single sentence > CHUNK_SIZE."""
    pieces, start = [], 0
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
        new_start = max(end - CHUNK_OVERLAP, start + 1)
        space = text.find(" ", new_start)
        if space != -1 and space < end:
            new_start = space + 1
        start = new_start
    return pieces


def _sentence_split(text):
    """Split an over-long line into <=CHUNK_SIZE pieces at sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    pieces, cur = [], ""
    for s in sentences:
        if len(s) > CHUNK_SIZE:           # a single monster sentence
            if cur:
                pieces.append(cur)
                cur = ""
            pieces.extend(_window(s))
        elif not cur:
            cur = s
        elif len(cur) + 1 + len(s) <= CHUNK_SIZE:
            cur += " " + s
        else:
            pieces.append(cur)
            cur = s
    if cur:
        pieces.append(cur)
    return pieces


def _pack_block(block):
    """Pack a block's lines into <=CHUNK_SIZE pieces, keeping whole lines together.

    A comment and its indented replies are separate lines in the same block, so
    they stay in one piece until the size limit; only a single over-long line
    (a very long comment) is split further, at sentence boundaries.
    """
    pieces, cur = [], ""
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        units = [line] if len(line) <= CHUNK_SIZE else _sentence_split(line)
        for u in units:
            if not cur:
                cur = u
            elif len(cur) + 1 + len(u) <= CHUNK_SIZE:
                cur += "\n" + u
            else:
                pieces.append(cur)
                cur = u
    if cur:
        pieces.append(cur)
    return pieces


def chunk_document(text, source):
    """
    Split a source document into chunks ready for embedding.

    Strategy: boundary-aware, opinions only.
      - Only the post (the question) and the comments (the advice) are embedded.
        The schedule is a timetable, not an opinion, so it is NOT a searchable
        chunk; it is kept on each chunk's metadata for grounding instead. The
        major/classification/semester ride along as metadata too.
      - Each top-level comment plus its nested replies = one block; it stays
        whole unless it exceeds CHUNK_SIZE.
      - chunk_size = 600 characters (~150 tokens, see planning.md). Only a block
        longer than this is split, and then at sentence boundaries so pieces are
        whole sentences rather than cut mid-thought.
      - min_length = 50 characters: drops fragments and bare labels.

    Returns a list of dicts, each with "text", "chunk_id", "section", and the
    document metadata (source, major, classification, semester, schedule).
    """
    meta, schedule, post, comments = parse_document(text)

    doc_meta = {
        "source": source,
        "url": meta.get("url", ""),
        "major": meta.get("major", ""),
        "classification": meta.get("classification", ""),
        "semester": meta.get("semester", ""),
        "schedule": schedule,
    }

    # Short context line prepended to each chunk's embedded text so the major
    # is part of what the embedder sees — this disambiguates the otherwise
    # near-identical "Rate my Schedule" threads (planning.md Challenge #2).
    ctx = "Context: " + (meta.get("major") or "student")
    if meta.get("semester"):
        ctx += f", {meta['semester']}"
    ctx += "."

    chunks = []
    counter = 0

    def emit(piece, section):
        nonlocal counter
        piece = piece.strip()
        if len(piece) >= MIN_CHUNK_LENGTH:
            chunks.append({
                "text": f"{ctx}\n{piece}",
                "chunk_id": f"{source}_{counter}",
                "section": section,
                **doc_meta,
            })
            counter += 1

    # NB: the original post is the OP asking "rate my schedule" — a question,
    # not advice. Embedding it makes it match query-questions and crowd out the
    # actual answers, so we do NOT embed posts. Only the comments (the advice)
    # are retrievable; the post's situation lives in the schedule/major metadata.

    # one block per comment thread (blank-line separated)
    for block in re.split(r"\n\s*\n", comments):
        for piece in _pack_block(block.strip()):
            emit(piece, "comment")

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
