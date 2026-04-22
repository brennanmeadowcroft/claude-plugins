---
name: index-meeting-note
description: Index a processed meeting note into the ChromaDB meeting memory store. Typically called automatically by /process-transcripts (Phase 6), but can be called directly to re-index a note or backfill historical meetings. Must be run from the vault root.
argument-hint: "[optional] --reindex-file <vault-relative-path>"
allowed-tools: Bash, Read, Glob
---

# Index Meeting Note

Save a processed meeting note section into the meeting memory vector store so it can be queried later with `/ask-meetings`.

## When called directly (manual or backfill)

If `--reindex-file <path>` is provided, re-index all dated sections in that notes file.

Otherwise, index a single note based on the context provided by the user or calling skill.

---

## Single-note indexing

Assemble the JSON record from context and pipe it to the script:

```bash
python3.13 .claude/skills/index-meeting-note/scripts/save_meeting_note.py <<'EOF'
{
  "content": "<full text of the meeting note section>",
  "date": "YYYY-MM-DD",
  "meeting_name": "<contact name for 1:1s, or meeting title>",
  "meeting_type": "1:1",
  "source_file": "<vault-relative path to the note file>",
  "project_tags": ["project-slug-1", "project-slug-2"],
  "attendees": "<contact name(s)>"
}
EOF
```

### Field guidance

- **content**: The full text of the `## YYYY-MM-DD` section (for recurring meetings) or the entire note body (for ad-hoc). Include the date heading and all subsections.
- **meeting_type**: Use `"1:1"` for direct-report or peer 1:1s; `"meeting"` for everything else.
- **project_tags**: For **1:1s** — infer from the summary: which projects were meaningfully discussed? Cross-reference `01-Projects/` to get canonical project folder names as slugs (lowercase, hyphen-separated). Leave empty `[]` if no specific project was a significant focus. For **ad-hoc meetings** — use the frontmatter `tags` array value (typically one project tag).
- **attendees**: For 1:1s, the contact's name. For ad-hoc meetings, leave as `""`.
- **source_file**: Vault-relative path, e.g. `02-AreasOfResponsibility/Notes/Craig Swank - 2026.md`.

---

## Backfill: re-indexing all sections in a notes file

To index all existing dated sections from a long-running recurring notes file, read the file and parse the `## YYYY-MM-DD` sections. For each section, call the single-note indexing command above with the appropriate date and content.

For 1:1 note files:
1. Use `Glob` to find the file: `02-AreasOfResponsibility/Notes/<Name> - <Year>.md`
2. Read the file and split on `^## \d{4}-\d{2}-\d{2}` to extract each section
3. For each section, infer project_tags from the content and run the index command
4. Report how many sections were indexed

---

## After indexing

Confirm to the user how many chunks were stored and for which meeting/date.
