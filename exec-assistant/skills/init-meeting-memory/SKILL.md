---
name: init-meeting-memory
description: Initialize the ChromaDB vector store for meeting memory. Installs dependencies, creates .gitignore entry, and smoke-tests the database. Run this once from the vault root before /ask-meetings or the auto-indexing in /process-transcripts will work.
argument-hint:
allowed-tools: Bash, Read, Write
---

# Initialize Meeting Memory

Set up the ChromaDB vector store for persisting processed meeting notes.

## Instructions

Run the init script from the vault root:

```bash
python3.13 .claude/skills/init-meeting-memory/scripts/init_meeting_memory.py
```

The script will:

1. Check that python3.13 is available
2. Install `chromadb` via pip (skips if already installed)
3. Append `.meeting-memory/` to `.gitignore` at the vault root (so Nextcloud does not sync it)
4. Initialize the ChromaDB persistent store and create the `meetings` collection as a smoke test
5. Report success or failure with clear next steps

## After Success

Tell the user:

- The vector store is ready at `.meeting-memory/` in the vault root
- Future `/process-transcripts` runs will automatically index each processed note
- Use `/ask-meetings <question>` to query the meeting history
- To backfill historical notes, use `/index-meeting-note --reindex-file <path>`
