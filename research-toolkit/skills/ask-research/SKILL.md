---
name: ask-research
description: Query the research vector store with a follow-up question. Searches previously collected research content (web pages, transcripts, analyses) using semantic search and synthesizes an answer with citations. Use after /deep-research to ask follow-up questions about the gathered material.
argument-hint: <your follow-up question>
allowed-tools: Bash, Read
---

# Ask Research

Query the ChromaDB vector store to answer follow-up questions about previously gathered research content.

## Instructions

1. **Analyze the user's question** (`$ARGUMENTS`) for implicit filters:
   - Question mentions "YouTube" or "videos" → add `--filter-type youtube`
   - Question mentions "web" or "articles" or "pages" → add `--filter-type web`
   - Question asks about "key findings" or "analysis" or "evaluation" → add `--filter-chunk-type analysis`
   - Question asks about "most credible" or "high confidence" or "reliable" → add `--min-confidence 7`
   - No implicit filter → search everything (default)

2. **Run the query script** with the question and any inferred flags:

```bash
python3.13 .claude/skills/ask-research/scripts/query_vectordb.py "$ARGUMENTS"
```

With filters example:

```bash
python3.13 .claude/skills/ask-research/scripts/query_vectordb.py --filter-type youtube --min-confidence 7 "What did experts say about document processing?"
```

3. **Synthesize a coherent answer** from the returned chunks:
   - Organize information thematically, not by chunk
   - Combine insights from multiple chunks into flowing paragraphs
   - Resolve any contradictions between sources
   - Note confidence levels when they vary significantly

4. **Cite sources** for every key claim:
   - Include the source title and URL
   - Note the confidence score
   - Format: "According to [Title](url) (confidence: 8/10), ..."

5. **If the query returns no results**, inform the user that:
   - The vector store may not be initialized (suggest `/init-research-toolkit`)
   - No research has been conducted yet (suggest `/deep-research <topic>`)
   - The question may not match any stored content (suggest rephrasing)

## Available Flags

| Flag | Values | Description |
|------|--------|-------------|
| `--filter-type` | `web`, `youtube` | Filter by source type |
| `--filter-chunk-type` | `content`, `analysis` | Filter by chunk type |
| `--min-confidence` | `1`-`10` | Minimum confidence score |
| `--top-k` | integer | Number of results (default: 10) |
