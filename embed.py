"""
Milestone 4 — Embed chunks into ChromaDB and test retrieval.

Pipeline: build_chunks() (Milestone 3)  ->  embed with all-MiniLM-L6-v2  ->
store in ChromaDB with metadata  ->  retrieve(query) returns top-k chunks.

  build_store()        (re)builds the persisted ChromaDB collection from scratch
  retrieve(query, k)   embeds a query and returns the k closest chunks + scores

Run directly to build the store and test it against the evaluation questions:
    python embed.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

from config import EMBED_MODEL, CHROMA_PATH, COLLECTION_NAME, TOP_K
from ingest import build_chunks

# Load the embedding model once (downloaded + cached on first run, no API key).
_model = SentenceTransformer(EMBED_MODEL)

# Persistent on-disk client so the store survives between runs.
_client = chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection():
    """Open the collection (cosine distance, to match the milestone's 0–1 scores)."""
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_store():
    """Embed every chunk and (re)load them into ChromaDB with metadata."""
    # Start clean so re-runs don't pile up duplicate ids.
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = get_collection()

    chunks = build_chunks()
    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    # everything except the text + id becomes searchable/attribution metadata
    metadatas = [
        {k: v for k, v in c.items() if k not in ("text", "chunk_id")}
        for c in chunks
    ]
    embeddings = _model.encode(documents, show_progress_bar=False).tolist()

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"Embedded and stored {collection.count()} chunks in '{COLLECTION_NAME}'.")
    return collection


def retrieve(query, k=TOP_K):
    """Return the k chunks closest to `query`, each with source + distance."""
    collection = get_collection()
    q_emb = _model.encode([query]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=k)

    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append({
            "text": doc,
            "source": meta.get("source", ""),
            "major": meta.get("major", ""),
            "distance": dist,
            "metadata": meta,
        })
    return results


# Three evaluation questions from planning.md: one broad (tests recall) and
# two specific (test precision against named professors/courses).
EVAL_QUERIES = [
    "What do students say about taking multiple 2000-level CS courses in the same semester?",
    "Should I take Nhut Nguyen or Alice Wang for CS 2340 Computer Architecture?",
    "What course sequence do students recommend for pre-med (gen chem, bio, ochem)?",
]


def main():
    build_store()
    print("\n" + "=" * 70)
    print("Retrieval test against evaluation questions (top-{}):".format(TOP_K))
    for q in EVAL_QUERIES:
        print("\n" + "-" * 70)
        print(f"QUERY: {q}")
        for i, r in enumerate(retrieve(q), 1):
            flag = "  <-- weak match" if r["distance"] > 0.6 else ""
            print(f"\n  [{i}] distance {r['distance']:.3f}  | "
                  f"source: {r['source']} | major: {r['major']}{flag}")
            text = r["text"].replace("\n", " ")
            print(f"      {text[:400]}{'...' if len(text) > 400 else ''}")


if __name__ == "__main__":
    main()
