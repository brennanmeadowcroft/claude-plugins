#!/usr/bin/env python3
"""Query the ChromaDB vector store for research content."""

import argparse
import json
import os
import sys


def find_project_root():
    """Walk up from cwd to find the directory containing .claude/."""
    d = os.path.abspath(os.getcwd())
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        d = os.path.dirname(d)
    return os.path.abspath(os.getcwd())


def main():
    parser = argparse.ArgumentParser(description="Query the research vector store")
    parser.add_argument("question", help="The question to search for")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to return")
    parser.add_argument("--filter-type", choices=["web", "youtube"], help="Filter by source type")
    parser.add_argument("--filter-chunk-type", choices=["content", "analysis"], help="Filter by chunk type")
    parser.add_argument("--min-confidence", type=int, choices=range(1, 11), help="Minimum confidence score (1-10)")
    args = parser.parse_args()

    project_root = find_project_root()
    db_path = os.path.join(project_root, ".research-memory")

    if not os.path.exists(db_path):
        result = {
            "status": "error",
            "message": "Vector store not found. Run /init-research-toolkit to set up the database.",
            "results": [],
        }
        print(json.dumps(result, indent=2))
        return

    try:
        import chromadb
    except ImportError:
        result = {
            "status": "error",
            "message": "chromadb not installed. Run /init-research-toolkit to install dependencies.",
            "results": [],
        }
        print(json.dumps(result, indent=2))
        return

    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(
            name="research",
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Could not connect to vector store: {e}",
            "results": [],
        }
        print(json.dumps(result, indent=2))
        return

    if collection.count() == 0:
        result = {
            "status": "empty",
            "message": "The vector store is empty. Run /deep-research to populate it with content.",
            "results": [],
        }
        print(json.dumps(result, indent=2))
        return

    # Build where clause from filters
    where_conditions = []

    if args.filter_type:
        where_conditions.append({"source_type": {"$eq": args.filter_type}})

    if args.filter_chunk_type:
        where_conditions.append({"chunk_type": {"$eq": args.filter_chunk_type}})

    if args.min_confidence:
        where_conditions.append({"confidence": {"$gte": args.min_confidence}})

    where = None
    if len(where_conditions) == 1:
        where = where_conditions[0]
    elif len(where_conditions) > 1:
        where = {"$and": where_conditions}

    # Query
    try:
        query_params = {
            "query_texts": [args.question],
            "n_results": min(args.top_k, collection.count()),
        }
        if where:
            query_params["where"] = where

        results = collection.query(**query_params)
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Query failed: {e}",
            "results": [],
        }
        print(json.dumps(result, indent=2))
        return

    # Format results
    formatted = []
    if results and results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            entry = {
                "id": doc_id,
                "text": results["documents"][0][i] if results["documents"] else "",
                "relevance_score": round(1 - results["distances"][0][i], 4) if results["distances"] else None,
                "url": results["metadatas"][0][i].get("url", "") if results["metadatas"] else "",
                "title": results["metadatas"][0][i].get("title", "") if results["metadatas"] else "",
                "source_type": results["metadatas"][0][i].get("source_type", "") if results["metadatas"] else "",
                "confidence": results["metadatas"][0][i].get("confidence", 0) if results["metadatas"] else 0,
                "chunk_type": results["metadatas"][0][i].get("chunk_type", "") if results["metadatas"] else "",
            }
            formatted.append(entry)

    output = {
        "status": "success",
        "question": args.question,
        "total_documents": collection.count(),
        "results_returned": len(formatted),
        "filters_applied": {
            "source_type": args.filter_type,
            "chunk_type": args.filter_chunk_type,
            "min_confidence": args.min_confidence,
        },
        "results": formatted,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
