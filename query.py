"""
Milestone 5 — Grounded generation.

ask(question) ties the pipeline together: retrieve the most relevant student
comments, then ask Groq's LLM to answer USING ONLY those comments. The system
prompt enforces grounding (no outside knowledge; say so when the context is
insufficient), and the source list is built programmatically from the retrieved
chunks' metadata — not left to the model to invent.

    from query import ask
    result = ask("Should I take Nguyen or Wang for CS 2340?")
    print(result["answer"])
    print(result["sources"])
"""

import os

from dotenv import load_dotenv
from groq import Groq

from config import GEN_MODEL, GEN_TEMPERATURE, TOP_K
from embed import retrieve

load_dotenv()
_client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = (
    "You are an assistant that helps UT Dallas students pick courses and "
    "professors. You answer ONLY from the student comments provided in the "
    "context — these are real opinions from r/utdallas 'Rate my Schedule' "
    "threads. Follow these rules strictly:\n"
    "1. Use ONLY the information in the provided context. Do NOT use any outside "
    "or general knowledge, and do not guess.\n"
    "2. If the context does not contain enough information to answer the "
    "question, reply with exactly: \"I don't have enough information on that.\" "
    "and nothing else.\n"
    "3. Attribute claims to the students (e.g., \"students say...\", \"one "
    "commenter recommends...\"). Note disagreement when the comments disagree.\n"
    "4. Be concise — only state what the comments actually support."
)


def _format_context(chunks):
    """Number the retrieved chunks and label each with its source for the prompt."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[{i}] (source: {c['source']})\n{c['text']}")
    return "\n\n".join(blocks)


def _sources(chunks):
    """Deduped, ordered source list built from metadata — guaranteed attribution."""
    seen, out = set(), []
    for c in chunks:
        src = c["source"]
        if src in seen:
            continue
        seen.add(src)
        url = c.get("metadata", {}).get("url", "")
        out.append(f"{src} ({url})" if url else src)
    return out


def ask(question, k=TOP_K):
    """Retrieve, generate a grounded answer, and return it with its sources."""
    chunks = retrieve(question, k=k)

    context = _format_context(chunks)
    user_prompt = (
        f"Context (student comments):\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above."
    )

    completion = _client.chat.completions.create(
        model=GEN_MODEL,
        temperature=GEN_TEMPERATURE,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    answer = completion.choices[0].message.content.strip()

    # When the model refuses (context didn't cover the question), there are no
    # real sources to cite — don't list the irrelevant retrieved chunks.
    refused = answer.lower().startswith("i don't have enough information")
    sources = [] if refused else _sources(chunks)

    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks,
    }


# Quick end-to-end check, including one out-of-domain question.
_TEST_QUESTIONS = [
    "Should I take Nhut Nguyen or Alice Wang for CS 2340 Computer Architecture?",
    "What course sequence do students recommend for pre-med (gen chem, bio, ochem)?",
    "What's the best dining hall at UT Dallas?",   # out of domain -> should refuse
]


def main():
    for q in _TEST_QUESTIONS:
        print("=" * 72)
        print("Q:", q)
        result = ask(q)
        print("\nANSWER:\n" + result["answer"])
        print("\nSOURCES:")
        for s in result["sources"]:
            print("  •", s)
        print()


if __name__ == "__main__":
    main()
