from __future__ import annotations

import os
import sys
from typing import List, Dict

from dotenv import load_dotenv
from groq import Groq, APIError

load_dotenv()

from retriever import retrieve

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
    lines = ["\nSources:"]
    for i, (source, url) in enumerate(seen.items(), 1):
        if url:
            lines.append(f"  [{i}] {source} — {url}")
        else:
            lines.append(f"  [{i}] {source}")
    return "\n".join(lines)


def generate_answer(query: str, client: Groq) -> None:
    chunks = retrieve(query)

    if not chunks:
        print("\nI don't have enough information in the retrieved sources to answer this question.\n")
        return

    context_block = _build_context_block(chunks)
    user_message = f"{context_block}\n\nQuestion: {query}"

    print()
    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            print(text, end="", flush=True)

    print(_build_sources_list(chunks))
    print()


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
            generate_answer(query, client)
        except APIError as e:
            print(f"\nAPI error: {e}\n")


if __name__ == "__main__":
    chat_loop()
