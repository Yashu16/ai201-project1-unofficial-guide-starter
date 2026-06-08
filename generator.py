from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

from config import (
    CHUNKS_PATH,
    MIN_CHUNK_TOKENS,
    NARRATIVE_CHUNK_TOKENS,
    NARRATIVE_OVERLAP_TOKENS,
    RAW_DOCUMENTS_PATH,
    SHORT_REVIEW_MAX_TOKENS,
)
from ingest import run_ingestion

TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def estimate_tokens(text: str) -> int:
    return len(TOKEN_RE.findall(text))


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _slice_by_token_window(tokens: List[str], chunk_size: int, overlap: int) -> List[str]:
    if not tokens:
        return []

    step = max(1, chunk_size - overlap)
    chunks: List[str] = []

    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        part = " ".join(tokens[start:end]).strip()
        if part:
            chunks.append(part)
        if end >= len(tokens):
            break
        start += step

    return chunks


def _line_based_chunks(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks: List[str] = []

    for line in lines:
        # Keep table-like records and bullets as atomic chunks.
        if "|" in line or line.startswith("-") or line.startswith("*"):
            chunks.append(line)
            continue

        # If a line is long, split it with zero overlap (structured source policy).
        tokens = TOKEN_RE.findall(line)
        if len(tokens) > NARRATIVE_CHUNK_TOKENS:
            chunks.extend(_slice_by_token_window(tokens, NARRATIVE_CHUNK_TOKENS, overlap=0))
        else:
            chunks.append(line)

    return chunks


def chunk_document(doc: Dict) -> List[Dict]:
    source_kind = (doc.get("source_kind") or "local").lower()
    doc_id = doc["doc_id"]
    text = clean_text(doc.get("text", ""))
    if not text:
        return []

    chunks: List[str]

    if source_kind in {"grades", "structured"}:
        chunks = _line_based_chunks(text)
    else:
        token_list = TOKEN_RE.findall(text)

        # Keep very short reviews/posts atomic for better attribution.
        if source_kind in {"review", "discussion"} and len(token_list) <= SHORT_REVIEW_MAX_TOKENS:
            chunks = [" ".join(token_list)]
        else:
            overlap = NARRATIVE_OVERLAP_TOKENS if source_kind in {"review", "discussion", "local"} else 0
            chunks = _slice_by_token_window(token_list, NARRATIVE_CHUNK_TOKENS, overlap)

    output = []
    for i, chunk_text in enumerate(chunks):
        token_count = estimate_tokens(chunk_text)
        if token_count < MIN_CHUNK_TOKENS and len(chunks) > 1:
            continue

        output.append(
            {
                "chunk_id": f"{doc_id}:{i}",
                "doc_id": doc_id,
                "title": doc.get("title"),
                "source": doc.get("source"),
                "source_kind": source_kind,
                "url": doc.get("url"),
                "text": chunk_text,
                "token_estimate": token_count,
                "metadata": doc.get("metadata", {}),
            }
        )

    return output


def chunk_documents(documents: List[Dict]) -> List[Dict]:
    all_chunks: List[Dict] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc))
    return all_chunks


def load_raw_documents(path: Path = RAW_DOCUMENTS_PATH) -> List[Dict]:
    if not path.exists():
        return []

    docs: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def save_chunks(chunks: List[Dict], output_path: Path = CHUNKS_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=True) + "\n")
    return output_path


def run_chunking(include_web: bool = True) -> Path:
    docs, _, _ = run_ingestion(include_web=include_web)
    chunks = chunk_documents(docs)
    output = save_chunks(chunks)

    print(f"Loaded {len(docs)} document(s).")
    print(f"Produced {len(chunks)} chunk(s).")
    print(f"Saved chunks to: {output}")

    return output


if __name__ == "__main__":
    run_chunking(include_web=True)
