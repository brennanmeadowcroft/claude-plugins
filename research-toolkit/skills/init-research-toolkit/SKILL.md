---
name: init-research-toolkit
description: Initialize the research toolkit — configures WebSearch/WebFetch permissions, installs ChromaDB, and sets up the vector store. Run this once per project before using /deep-research or /ask-research.
argument-hint:
allowed-tools: Bash, Read, Write
---

# Initialize Research Toolkit

Set up everything needed for the research toolkit to function in this project.

## Instructions

Run the init script:

```bash
python3.13 .claude/skills/init-research-toolkit/scripts/init_research_toolkit.py
```

The script will:

1. **Check permissions** — ensures `WebSearch` and `WebFetch` are in `.claude/settings.json` `permissions.allow` (adds them if missing)
2. **Check python3.13** is available
3. **Check yt-dlp** is available (warns if missing but doesn't block — only needed for YouTube research)
4. **Install chromadb** via pip (skips if already installed)
5. **Set up .gitignore** — appends `.research-memory/` (creates the file if needed)
6. **Smoke test** — initializes the ChromaDB persistent store and creates the `research` collection

## After Success

Tell the user:

- The research toolkit is ready to use
- WebSearch and WebFetch permissions are configured for this project
- The vector store is ready at `.research-memory/`
- Research agents will automatically save content to the vector store during `/deep-research`
- Use `/ask-research <question>` to query the stored research content
