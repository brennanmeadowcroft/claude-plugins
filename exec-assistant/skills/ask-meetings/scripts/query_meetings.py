#!/usr/bin/env python3
"""Query the ChromaDB meeting memory store.

Usage:
    python3.13 query_meetings.py [OPTIONS] "question"

Options:
    --meeting-type 1:1|meeting   Filter by meeting type
    --project SLUG               Filter by project tag (substring match)
    --from-date YYYY-MM-DD       Earliest meeting date (inclusive)
    --to-date YYYY-MM-DD         Latest meeting date (inclusive)
    --top-k N                    Number of results to return (default: 10)

Output: JSON with status, results list, and metadata.
"""

import argparse
import json
import os
import sys


def find_vault_root():
    """Walk up from CWD to find the directory containing .claude/."""
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()


def build_where_clause(args):
    """Build ChromaDB where clause from date and meeting_type filters.

    Note: project filtering is done post-query (substring match on project_tags
    is not supported natively in ChromaDB metadata).
    """
    conditions = []

    if args.meeting_type:
        conditions.append({"meeting_type": {"$eq": args.meeting_type}})

    if args.from_date:
        conditions.append({"date": {"$gte": args.from_date}})

    if args.to_date:
        conditions.append({"date": {"$lte": args.to_date}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def filter_by_project(results, project_slug):
    """Post-filter results to those where project_tags contains the slug."""
    if not project_slug:
        return results
    slug = project_slug.lower()
    filtered = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    for i, meta in enumerate(results["metadatas"][0]):
        tags = meta.get("project_tags", "").lower()
        if slug in tags:
            filtered["ids"][0].append(results["ids"][0][i])
            filtered["documents"][0].append(results["documents"][0][i])
            filtered["metadatas"][0].append(results["metadatas"][0][i])
            filtered["distances"][0].append(results["distances"][0][i])
    return filtered


def main():
    parser = argparse.ArgumentParser(description="Query the meeting memory vector store")
    parser.add_argument("question", help="The question to search for")
    parser.add_argument("--meeting-type", choices=["1:1", "meeting"], help="Filter by meeting type")
    parser.add_argument("--project", help="Filter by project slug (substring match on project_tags)")
    parser.add_argument("--from-date", help="Earliest date to include (YYYY-MM-DD, inclusive)")
    parser.add_argument("--to-date", help="Latest date to include (YYYY-MM-DD, inclusive)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to return (default: 10)")
    args = parser.parse_args()

    vault_root = find_vault_root()
    db_path = os.path.join(vault_root, ".meeting-memory")

    if not os.path.exists(db_path):
        print(json.dumps({
            "status": "error",
            "message": "Meeting memory store not found. Run /init-meeting-memory to set it up.",
            "results": [],
        }, indent=2))
        return

    try:
        import chromadb
    except ImportError:
        print(json.dumps({
            "status": "error",
            "message": "chromadb not installed. Run /init-meeting-memory to install dependencies.",
            "results": [],
        }, indent=2))
        return

    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(
            name="meetings",
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"Could not connect to meeting memory store: {e}",
            "results": [],
        }, indent=2))
        return

    total_docs = collection.count()
    if total_docs == 0:
        print(json.dumps({
            "status": "empty",
            "message": "No meeting notes indexed yet. Run /process-transcripts to index meetings, or /index-meeting-note to backfill.",
            "results": [],
        }, indent=2))
        return

    where = build_where_clause(args)

    # When filtering by project we need to over-fetch and post-filter
    fetch_k = args.top_k * 3 if args.project else args.top_k
    fetch_k = min(fetch_k, total_docs)

    try:
        query_params = {
            "query_texts": [args.question],
            "n_results": fetch_k,
        }
        if where:
            query_params["where"] = where

        raw = collection.query(**query_params)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"Query failed: {e}",
            "results": [],
        }, indent=2))
        return

    # Post-filter by project if needed, then truncate to top_k
    if args.project:
        raw = filter_by_project(raw, args.project)

    formatted = []
    if raw and raw["ids"] and raw["ids"][0]:
        for i, doc_id in enumerate(raw["ids"][0][: args.top_k]):
            meta = raw["metadatas"][0][i] if raw["metadatas"] else {}
            formatted.append({
                "id": doc_id,
                "text": raw["documents"][0][i] if raw["documents"] else "",
                "relevance_score": round(1 - raw["distances"][0][i], 4) if raw["distances"] else None,
                "date": meta.get("date", ""),
                "meeting_name": meta.get("meeting_name", ""),
                "meeting_type": meta.get("meeting_type", ""),
                "source_file": meta.get("source_file", ""),
                "project_tags": meta.get("project_tags", ""),
                "attendees": meta.get("attendees", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "total_chunks": meta.get("total_chunks", 1),
            })

    print(json.dumps({
        "status": "success",
        "question": args.question,
        "total_documents": total_docs,
        "results_returned": len(formatted),
        "filters_applied": {
            "meeting_type": args.meeting_type,
            "project": args.project,
            "from_date": args.from_date,
            "to_date": args.to_date,
        },
        "results": formatted,
    }, indent=2))


if __name__ == "__main__":
    main()
