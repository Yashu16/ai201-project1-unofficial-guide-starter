from __future__ import annotations

import os
import sys
from typing import List, Dict, Generator

from dotenv import load_dotenv
from groq import Groq, APIError
import gradio as gr

from retriever import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a helpful academic advisor for UMD (University of Maryland) CS students.
You answer questions EXCLUSIVELY using the retrieved source chunks provided in the user message.
You must NOT use any knowledge from your training data.

Rules:
- If the provided chunks contain enough information to answer the question, answer it clearly and concisely.
- If the chunks do not contain sufficient information, respond with exactly:
  "I don't have enough information in the retrieved sources to answer this question."
- Never fabricate, infer beyond what is stated, or supplement with outside knowledge.
- Attribute your answer to the sources (e.g., "According to PlanetTerp reviews..." or "Reddit students mention...").
- Keep answers focused and grounded in the exact text of the chunks."""


def _build_context_block(chunks: List[Dict]) -> str:
    if not chunks:
        return ""
    lines = ["--- RETRIEVED SOURCES ---"]
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "Unknown source")
        url = chunk.get("url", "")
        lines.append(f"\n[{i}] {source}")
        if url:
            lines.append(f"    URL: {url}")
        lines.append(f"    {chunk['text']}")
    lines.append("\n--- END OF SOURCES ---")
    return "\n".join(lines)


def _build_sources_list(chunks: List[Dict]) -> str:
    if not chunks:
        return ""
    seen: dict[str, str] = {}
    for chunk in chunks:
        source = chunk.get("source", "Unknown source")
        url = chunk.get("url", "")
        if source not in seen:
            seen[source] = url
    lines = ["\n\n---\n**Sources:**"]
    for i, (source, url) in enumerate(seen.items(), 1):
        if url:
            lines.append(f"- [{source}]({url})")
        else:
            lines.append(f"- {source}")
    return "\n".join(lines)


def _get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set.")
    return Groq(api_key=api_key)


def stream_answer(query: str, client: Groq) -> Generator[str, None, None]:
    """Yields the answer token-by-token, then appends the sources block."""
    chunks = retrieve(query)

    if not chunks:
        yield "I don't have enough information in the retrieved sources to answer this question."
        return

    context_block = _build_context_block(chunks)
    user_message = f"{context_block}\n\nQuestion: {query}"

    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    full_text = ""
    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            full_text += text
            yield full_text

    yield full_text + _build_sources_list(chunks)


# ── Gradio UI ──────────────────────────────────────────────────────────────────

def _gradio_respond(message: str, history: list) -> Generator[str, None, None]:
    client = _get_client()
    yield from stream_answer(message, client)


def launch_ui() -> None:
    demo = gr.ChatInterface(
        fn=_gradio_respond,
        title="UMD CS Unofficial Guide",
        description=(
            "Ask about UMD CS courses, professors, exams, or grades. "
            "Answers are grounded in student reviews and official sources."
        ),
        examples=[
            "Which CMSC professor is known for giving the most useful feedback?",
            "Is CMSC351 actually as hard as people say?",
            "What do students wish they knew before taking CMSC216?",
            "Is the CS internship scene at UMD competitive?",
        ],
        cache_examples=False,
    )
    demo.launch()


# ── Terminal fallback ──────────────────────────────────────────────────────────

def chat_loop() -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable is not set.")
        sys.exit(1)

    client = Groq(api_key=api_key)

    print("UMD CS Unofficial Guide — powered by Groq")
    print("Ask anything about UMD CS courses, professors, exams, or grades.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            query = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        try:
            print()
            for partial in stream_answer(query, client):
                print(f"\r{partial}", end="", flush=True)
            print()
        except APIError as e:
            print(f"\nAPI error: {e}\n")


if __name__ == "__main__":
    if "--terminal" in sys.argv:
        chat_loop()
    else:
        launch_ui()
