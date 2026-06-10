"""
Milestone 5 — Gradio web interface for The Unofficial Guide.

A viewer types a question; the app retrieves relevant r/utdallas student
comments, generates a grounded answer with Groq, and shows the answer plus the
threads it was retrieved from.

    python app.py   ->   open http://localhost:7860
"""

import gradio as gr

from query import ask


def handle_query(question):
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "— (no matching student comments)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide — UTD") as demo:
    gr.Markdown(
        "# The Unofficial Guide — UT Dallas\n"
        "Ask about UTD courses and professors. Answers come **only** from real "
        "student comments in r/utdallas \"Rate my Schedule\" threads — not from "
        "general knowledge. If the threads don't cover it, the app says so."
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. Should I take Nhut Nguyen or Alice Wang for CS 2340?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    gr.Examples(
        examples=[
            "Should I take Nhut Nguyen or Alice Wang for CS 2340 Computer Architecture?",
            "What course sequence do students recommend for pre-med (gen chem, bio, ochem)?",
            "What do students think of Professor Schulze for history?",
        ],
        inputs=inp,
    )

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
