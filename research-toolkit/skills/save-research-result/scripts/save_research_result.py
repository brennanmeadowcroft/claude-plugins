#!/usr/bin/env python3
"""Save a single research source result to the JSON results file and vector store.

Usage:
    python3 save_research_result.py <folder-path> <<'RESULT'
    {
      "url": "https://example.com",
      "title": "Page Title",
      "source_type": "web",
      "content": "<full page content or transcript — for vector store only>",
      "confidence": 8,
      "snippet": "Brief summary",
      "source_evaluation": {
        "authority": 9, "recency": 7, "accuracy": 8, "bias": 6, "relevance": 9
      },
      "key_findings": "...",
      "analysis": "...",
      "gaps": "..."
    }
    RESULT

- source_type "web"     → writes to <folder>/web-results.json
- source_type "youtube" → writes to <folder>/youtube-results.json
- "content" is sent to the vector store only; it is NOT stored in the JSON file.
- Vector store errors are non-fatal warnings and will not block the JSON write.
"""

import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile


# ---------------------------------------------------------------------------
# JSON file helpers
# ---------------------------------------------------------------------------

def resolve_results_path(folder_path, source_type):
    filename = "youtube-results.json" if source_type == "youtube" else "web-results.json"
    return os.path.join(folder_path, filename)


def write_to_json(results_path, url, entry):
    """Atomically merge one URL entry into the results JSON object using flock."""
    dir_path = os.path.dirname(os.path.abspath(results_path))
    os.makedirs(dir_path, exist_ok=True)

    lock_path = results_path + ".lock"
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        # Read existing data
        data = {}
        if os.path.exists(results_path):
            try:
                with open(results_path, "r") as f:
                    content = f.read().strip()
                if content:
                    data = json.loads(content)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: could not read existing file, starting fresh: {e}", file=sys.stderr)

        data[url] = entry

        # Write atomically via temp file
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", dir=dir_path, suffix=".tmp", delete=False
            ) as tmp:
                json.dump(data, tmp, indent=2)
                tmp.write("\n")
                tmp_path = tmp.name
            os.replace(tmp_path, results_path)
        except OSError as e:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise e
        # flock released when lock_file closes

    return len(data)


# ---------------------------------------------------------------------------
# Vector store helpers (non-fatal on any error)
# ---------------------------------------------------------------------------

def split_sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p for p in parts if p.strip()]


def chunk_content(text, target_words=600, overlap_words=100, min_words=100):
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        return [text] if text.strip() else []

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

    return chunks if chunks else [text]


def make_id(url, chunk_type, index):
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
    return f"{url_hash}-{chunk_type}-{index:03d}"


def fix_db_permissions(db_path):
    for dirpath, _, filenames in os.walk(db_path):
        os.chmod(dirpath, 0o755)
        for filename in filenames:
            os.chmod(os.path.join(dirpath, filename), 0o644)


def find_project_root():
    """Walk up from cwd to find the directory containing .claude/."""
    d = os.path.abspath(os.getcwd())
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        d = os.path.dirname(d)
    return os.path.abspath(os.getcwd())


def save_to_vectordb(record):
    """Save content + analysis to ChromaDB. All errors are non-fatal."""
    try:
        import chromadb
    except ImportError:
        print("  vectordb: chromadb not installed (run /init-research-toolkit to enable)", file=sys.stderr)
        return

    project_root = find_project_root()
    db_path = os.path.join(project_root, ".research-memory")

    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(
            name="research",
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        print(f"  vectordb: could not connect — {e}", file=sys.stderr)
        return

    url = record["url"]
    title = record["title"]
    source_type = record["source_type"]
    confidence = record["confidence"]

    content_chunks = chunk_content(record.get("content", ""))
    analysis_text = "\n\n".join(filter(None, [
        record.get("key_findings", ""),
        record.get("analysis", ""),
        record.get("gaps", ""),
    ]))
    analysis_chunks = chunk_content(analysis_text) if analysis_text.strip() else []

    all_ids, all_documents, all_metadatas = [], [], []

    for i, chunk in enumerate(content_chunks):
        all_ids.append(make_id(url, "content", i))
        all_documents.append(chunk)
        all_metadatas.append({
            "url": url, "title": title, "source_type": source_type,
            "confidence": confidence, "chunk_type": "content",
            "chunk_index": i, "total_chunks": len(content_chunks),
        })

    for i, chunk in enumerate(analysis_chunks):
        all_ids.append(make_id(url, "analysis", i))
        all_documents.append(chunk)
        all_metadatas.append({
            "url": url, "title": title, "source_type": source_type,
            "confidence": confidence, "chunk_type": "analysis",
            "chunk_index": i, "total_chunks": len(analysis_chunks),
        })

    if not all_ids:
        print("  vectordb: no content to save (empty after chunking)", file=sys.stderr)
        return

    try:
        collection.upsert(ids=all_ids, documents=all_documents, metadatas=all_metadatas)
        print(f"  vectordb: saved {len(content_chunks)} content + {len(analysis_chunks)} analysis chunk(s)")
    except Exception as e:
        print(f"  vectordb: upsert failed — {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: save_research_result.py <folder-path>", file=sys.stderr)
        sys.exit(1)

    folder_path = sys.argv[1]

    raw = sys.stdin.read().strip()
    if not raw:
        print("Error: no JSON data on stdin.", file=sys.stderr)
        sys.exit(1)

    try:
        record = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)

    required = ["url", "title", "source_type", "confidence", "key_findings", "analysis", "gaps"]
    missing = [f for f in required if f not in record]
    if missing:
        print(f"Error: missing required fields: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    url = record["url"]
    source_type = record["source_type"]

    # Build the JSON entry — exclude url (becomes the key) and content (vectordb only)
    entry = {k: v for k, v in record.items() if k not in ("url", "content")}

    # 1. Write to results JSON file
    results_path = resolve_results_path(folder_path, source_type)
    try:
        total = write_to_json(results_path, url, entry)
        print(f"Saved to {results_path} ({total} total entries): {url}")
    except OSError as e:
        print(f"Error: failed to write JSON results: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Save to vector store (non-fatal)
    save_to_vectordb(record)


if __name__ == "__main__":
    main()
