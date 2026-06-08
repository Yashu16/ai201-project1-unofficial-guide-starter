from __future__ import annotations

import re
from typing import List, Dict, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from config import (
    CHROMA_PATH,
    CHROMA_COLLECTION,
    EMBEDDING_MODEL,
    TOP_K_DEFAULT,
    TOP_K_SHORT,
    SHORT_CHUNK_TOKEN_THRESHOLD,
    RETRIEVAL_SCORE_CUTOFF,
)

_model: Optional[SentenceTransformer] = None
_collection: Optional[chromadb.Collection] = None


def _extract_course_code(query: str) -> Optional[str]:
    match = re.search(r"\bCMSC\s*(\d{3}[A-Z]?)\b", query, re.IGNORECASE)
    return f"CMSC{match.group(1).upper()}" if match else None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_collection(collection_name: str = CHROMA_COLLECTION) -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = client.get_collection(collection_name)
    return _collection


def retrieve(
    query: str,
    top_k: Optional[int] = None,
    source_kind: Optional[str] = None,
    score_cutoff: float = RETRIEVAL_SCORE_CUTOFF,
) -> List[Dict]:
    """Return the top-k most relevant chunks for *query*.

    Args:
        query: The user's natural-language question.
        top_k: How many results to return. Auto-selected from config if None.
        source_kind: Optional filter — e.g. "review", "discussion", "structured".
        score_cutoff: L2 distance ceiling; chunks above this are dropped.

    Returns:
        List of dicts with keys: chunk_id, text, source, source_kind, url, title,
        token_estimate, score, and any extra metadata fields.
    """
    model = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query]).tolist()

    course_code = _extract_course_code(query)

    if course_code and source_kind:
        where_filter = {"$and": [{"course": course_code}, {"source_kind": source_kind}]}
    elif course_code:
        where_filter = {"course": course_code}
    elif source_kind:
        where_filter = {"source_kind": source_kind}
    else:
        where_filter = None

    # We fetch a generous candidate set and then trim by score cutoff.
    fetch_k = max((top_k or TOP_K_DEFAULT) * 3, 15)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(fetch_k, collection.count()),
        where=where_filter,  # type: ignore[arg-type]
        include=["documents", "metadatas", "distances"],
    )

    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    candidates = []
    for cid, doc, meta, dist in zip(ids, docs, metas, distances):
        if dist <= score_cutoff:
            entry = {"chunk_id": cid, "text": doc, "score": dist}
            entry.update(meta)
            candidates.append(entry)

    # Determine top_k based on average token size when not specified.
    if top_k is None:
        avg_tokens = (
            sum(c.get("token_estimate", 0) for c in candidates) / len(candidates)
            if candidates
            else TOP_K_DEFAULT
        )
        top_k = TOP_K_SHORT if avg_tokens <= SHORT_CHUNK_TOKEN_THRESHOLD else TOP_K_DEFAULT

    return candidates[:top_k]


def print_results(results: List[Dict]) -> None:
    if not results:
        print("No results found above score cutoff.")
        return
    for i, r in enumerate(results, 1):
        print(f"\n--- Result {i} (score={r['score']:.4f}) ---")
        print(f"Source : {r.get('source', '')}  [{r.get('source_kind', '')}]")
        print(f"URL    : {r.get('url', '')}")
        print(f"Text   : {r['text'][:300]}{'…' if len(r['text']) > 300 else ''}")


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Which CMSC professor gives the most useful feedback?"
    print(f"Query: {query}\n")
    results = retrieve(query)
    print_results(results)
