#!/usr/bin/env python3
"""Index a processed meeting note section into the ChromaDB meeting memory store.

Usage (single note, piped JSON):
    python3.13 save_meeting_note.py <<'EOF'
    {
      "content": "## 2026-04-17\n### Summary\n...",
      "date": "2026-04-17",
      "meeting_name": "Craig Swank",
      "meeting_type": "1:1",
      "source_file": "02-AreasOfResponsibility/Notes/Craig Swank - 2026.md",
      "project_tags": ["project-x", "project-y"],
      "attendees": "Craig Swank"
    }
    EOF

    - project_tags: list of project slugs inferred from the transcript. All chunks
      from this transcript get the same tags (stored as a comma-joined string).
    - Vector store errors are non-fatal; the exit code is 0 even on DB failure.
    - Upserting with the same source_file+date is safe and idempotent.
"""

import hashlib
import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Chunking helpers (adapted from research-toolkit)
# ---------------------------------------------------------------------------

def split_sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p for p in parts if p.strip()]


def chunk_content(text, target_words=600, overlap_words=100, min_words=100):
    """Split text into overlapping chunks of ~target_words words."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        return [text] if text.strip() else []

    # Short content: store as a single chunk
    total_words = len(text.split())
    if total_words <= min_words * 2:
        return [text.strip()]

    expanded = []
    for para in paragraphs:
        word_count = len(para.split())
        if word_count > target_words * 1.5:
            sentences = split_sentences(para)
            current, current_words = [], 0
            for sent in sentences:
                sent_words = len(sent.split())
                if current_words + sent_words > target_words and current:
                    expanded.append(" ".join(current))
                    current, current_words = [sent], sent_words
                else:
                    current.append(sent)
                    current_words += sent_words
            if current:
                expanded.append(" ".join(current))
        else:
            expanded.append(para)

    chunks, current_chunk, current_words = [], [], 0
    for para in expanded:
        para_words = len(para.split())
        if current_words + para_words > target_words and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            overlap_parts, overlap_count = [], 0
            for p in reversed(current_chunk):
                p_words = len(p.split())
                if overlap_count + p_words > overlap_words and overlap_parts:
                    break
                overlap_parts.insert(0, p)
                overlap_count += p_words
            current_chunk = overlap_parts + [para]
            current_words = overlap_count + para_words
        else:
            current_chunk.append(para)
            current_words += para_words

    if current_chunk:
        last_chunk = "\n\n".join(current_chunk)
        if chunks and len(last_chunk.split()) < min_words:
            chunks[-1] = chunks[-1] + "\n\n" + last_chunk
        else:
            chunks.append(last_chunk)

    return chunks if chunks else [text.strip()]


def make_chunk_id(source_file, date, index):
    key = f"{source_file}::{date}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()[:12]
    return f"{key_hash}-{index:03d}"


# ---------------------------------------------------------------------------
# Vector store
# ---------------------------------------------------------------------------

def find_vault_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()


def fix_db_permissions(db_path):
    for dirpath, _, filenames in os.walk(db_path):
        os.chmod(dirpath, 0o755)
        for filename in filenames:
            os.chmod(os.path.join(dirpath, filename), 0o644)


def save_to_vectordb(record):
    """Save content chunks to ChromaDB. Non-fatal on any error."""
    try:
        import chromadb
    except ImportError:
        print("  meeting-memory: chromadb not installed (run /init-meeting-memory)", file=sys.stderr)
        return

    vault_root = find_vault_root()
    db_path = os.path.join(vault_root, ".meeting-memory")

    if not os.path.isdir(db_path):
        print("  meeting-memory: store not found — run /init-meeting-memory first", file=sys.stderr)
        return

    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(
            name="meetings",
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        print(f"  meeting-memory: could not connect — {e}", file=sys.stderr)
        return

    content = record.get("content", "")
    if not content.strip():
        print("  meeting-memory: empty content, skipping", file=sys.stderr)
        return

    chunks = chunk_content(content)
    project_tags_str = ",".join(record.get("project_tags", []))

    # Shared metadata for all chunks from this transcript
    base_meta = {
        "date": record["date"],
        "meeting_name": record["meeting_name"],
        "meeting_type": record["meeting_type"],
        "source_file": record["source_file"],
        "project_tags": project_tags_str,
        "attendees": record.get("attendees", ""),
        "total_chunks": len(chunks),
    }

    ids, documents, metadatas = [], [], []
    source_file = record["source_file"]
    date = record["date"]

    for i, chunk in enumerate(chunks):
        ids.append(make_chunk_id(source_file, date, i))
        documents.append(chunk)
        metadatas.append({**base_meta, "chunk_index": i})

    try:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        fix_db_permissions(db_path)
        print(f"  meeting-memory: indexed {len(chunks)} chunk(s) for {record['meeting_name']} on {date}")
    except Exception as e:
        print(f"  meeting-memory: upsert failed — {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    raw = sys.stdin.read().strip()
    if not raw:
        print("Error: no JSON data on stdin.", file=sys.stderr)
        sys.exit(1)

    try:
        record = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)

    required = ["content", "date", "meeting_name", "meeting_type", "source_file"]
    missing = [f for f in required if f not in record]
    if missing:
        print(f"Error: missing required fields: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Ensure project_tags is a list
    if "project_tags" not in record:
        record["project_tags"] = []
    elif isinstance(record["project_tags"], str):
        record["project_tags"] = [t.strip() for t in record["project_tags"].split(",") if t.strip()]

    save_to_vectordb(record)


if __name__ == "__main__":
    main()
