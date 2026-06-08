from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer

from config import (
    CHUNKS_PATH,
    CHROMA_PATH,
    CHROMA_COLLECTION,
    EMBEDDING_MODEL,
)


def load_chunks(path: Path = CHUNKS_PATH) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found: {path}. Run generator.py first.")
    chunks = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def build_vector_store(
    chunks: List[Dict],
    chroma_path: Path = CHROMA_PATH,
    collection_name: str = CHROMA_COLLECTION,
    model_name: str = EMBEDDING_MODEL,
) -> chromadb.Collection:
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]

    # Build metadata dicts — Chroma requires scalar values only.
    metadatas = []
    for c in chunks:
        meta = {
            "doc_id": c.get("doc_id") or "",
            "source": c.get("source") or "",
            "source_kind": c.get("source_kind") or "",
            "url": c.get("url") or "",
            "title": c.get("title") or "",
            "token_estimate": c.get("token_estimate") or 0,
        }
        # Flatten any nested metadata fields (professor, course, etc.)
        for k, v in (c.get("metadata") or {}).items():
            if isinstance(v, (str, int, float, bool)):
                meta[k] = v
        metadatas.append(meta)

    print(f"Embedding {len(texts)} chunks …")
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True).tolist()

    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path))

    # Drop and recreate so re-runs don't duplicate entries.
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "l2"},
    )

    # Chroma has a batch-size limit; upsert in pages of 5000.
    batch = 5000
    for start in range(0, len(ids), batch):
        collection.add(
            ids=ids[start : start + batch],
            embeddings=embeddings[start : start + batch],
            documents=texts[start : start + batch],
            metadatas=metadatas[start : start + batch],
        )

    print(f"Stored {collection.count()} embeddings in '{collection_name}' at {chroma_path}")
    return collection


def run_embedding() -> chromadb.Collection:
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks.")
    return build_vector_store(chunks)


if __name__ == "__main__":
    run_embedding()
