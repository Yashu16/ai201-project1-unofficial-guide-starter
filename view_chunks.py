#!/usr/bin/env python3
"""View sample chunks from chunks.jsonl with formatted metadata."""

import json
import sys
from pathlib import Path

from config import CHUNKS_PATH


def print_chunk(chunk: dict, num: int) -> None:
    """Print a single chunk with metadata."""
    print(f"\n{'='*80}")
    print(f"CHUNK {num}")
    print(f"{'='*80}")
    print(f"\n📌 METADATA:")
    print(f"  Chunk ID:    {chunk['chunk_id']}")
    print(f"  Doc ID:      {chunk['doc_id']}")
    print(f"  Title:       {chunk['title']}")
    print(f"  Source:      {chunk['source']}")
    print(f"  Source Kind: {chunk['source_kind']}")
    print(f"  URL:         {chunk['url']}")
    print(f"  Tokens:      {chunk['token_estimate']}")
    if chunk['metadata']:
        print(f"  Metadata:    {chunk['metadata']}")

    print(f"\n📄 TEXT ({len(chunk['text'])} chars):")
    # Show first 500 chars
    preview = chunk['text'][:500]
    if len(chunk['text']) > 500:
        preview += "..."
    print(f"  {preview}")


def view_chunks(num_chunks: int = 5, sample_lines: list = None) -> None:
    """View random or specified chunks."""
    if not CHUNKS_PATH.exists():
        print(f"Error: {CHUNKS_PATH} not found. Run `python generator.py` first.")
        sys.exit(1)

    # Default sample lines if not provided
    if sample_lines is None:
        sample_lines = [100, 500, 1500, 3000, 4500]

    with open(CHUNKS_PATH, encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if idx - 1 in sample_lines:
                chunk = json.loads(line)
                print_chunk(chunk, sample_lines.index(idx - 1) + 1)

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    # You can customize here:
    # view_chunks(sample_lines=[0, 100, 500, 1000, 2000])
    view_chunks()
