---
name: start-day
description: Morning briefing — pulls today's Google Calendar events and Todoist tasks, finds relevant meeting notes in Obsidian by searching for today's date, and synthesizes a prioritized daily plan. Optionally creates today's daily note. Trigger when the user says "start my day", "morning briefing", or invokes /start-day.
argument-hint: "[--daily-notes-path <path>] [--notes-path <path>]"
---

# Start Day

You are helping the user plan their day. Pull data from their three productivity tools, synthesize it into a clear morning briefing, and optionally create today's daily note.

Default paths (override with arguments):
- Daily notes: `Daily Notes/` (e.g., `Daily Notes/2026-03-30.md`)
- Meeting notes: `Notes/`

## Phase 0: Pre-Flight Check

1. Get today's date by running `date +%Y-%m-%d` via Bash. Store this as TODAY (e.g., `2026-03-30`). Also get the day name: `date +%A`.
2. Get today's timezone by calling `get-current-time` on the google-calendar server.
3. Verify each MCP server is reachable by attempting a lightweight call:
   - **Todoist**: call `get_tasks` with an empty or minimal filter
   - **Google Calendar**: already verified via `get-current-time`
   - **Obsidian**: call `search_notes` with query `daily-note`

If any server fails, STOP and tell the user exactly which server is unreachable and the `claude mcp add` command from the README to fix it. Do NOT proceed without all three servers.

## Phase 1: Gather Today's Data

Run these in parallel where possible:

**Calendar:** Call `list-events` for today (midnight to midnight in the user's timezone). For each event capture: title, start/end time, attendees, video call link if present.

**Todoist — due today:** Call `get_tasks` filtered to tasks due today. For each task capture: name, project, priority (p1–p4), any due time.

**Todoist — overdue:** Call `get_tasks` filtered to overdue tasks. For each task note how many days overdue.

**Meeting notes for today:** Call `search_notes` with the query TODAY (the date string, e.g., `2026-03-30`). This surfaces any long-running meeting note that has a section for today — no manual tagging needed. The section was added by `/finish-day` the previous evening.

**Existing daily note:** Attempt `read_note` on `<daily-notes-path>/TODAY.md`. If it exists, read its content — the user may have already started it.

## Phase 2: Synthesize Morning Briefing

Present the briefing in this structure:

---

### Good [morning/afternoon] — [Day Name], [Full Date]

**At a Glance**
[X] calendar events · [Y] tasks due today · [Z] overdue

**Calendar**
List events chronologically with start and end times. Flag any day with more than 4 hours of back-to-back meetings. Include a note link (e.g., `[[Meeting Name]]`) if a matching meeting note was found in Phase 1.

**Top Priorities**
Synthesize Todoist p1 and p2 tasks into a ranked list of 3–5 focus areas. Briefly explain the ranking (e.g., "p1, overdue 2 days"). Keep it scannable.

**Overdue Items**
List overdue tasks grouped by how overdue they are. For anything overdue more than 3 days, flag it explicitly.

**Suggested Focus Blocks** (include only if there are clear gaps in the calendar)
Based on gaps between calendar events, suggest 1–3 focus windows for deep work. Example: "9:00–11:00 — clear window before standup, good for [top priority task]."

**Today's Meeting Notes**
If meeting notes were found for today (Phase 1), list them with their Obsidian note title and a brief reminder of context if visible in the section content.

---

## Phase 3: Create Daily Note (optional)

Ask: "Would you like me to create today's daily note in Obsidian?"

If yes (or if the user passed `--create-daily-note`):
- If no daily note exists, use `write_note` to create `<daily-notes-path>/TODAY.md` with this template:

```markdown
---
date: TODAY
tags: [daily-note]
---

# [Day Name], [Full Date]

## Morning Intentions

[Top 3 priorities from Phase 2]

## Schedule

[Calendar events from Phase 1, one per line with times]

## Meeting Notes

[Links to today's relevant meeting notes found in Phase 1, e.g., [[1:1 with Alex]], [[Team Standup]]]

## Notes

## End of Day
<!-- Filled in by /finish-day -->
```

- If a daily note already exists, use `patch_note` to add or update only the "Morning Intentions" section rather than overwriting the file.

## Quality Notes

- Always use the date from Bash (`date` command), never infer it
- Priorities should reflect both urgency (due dates, overdue status) and importance (Todoist priority levels)
- Keep the briefing scannable — headers and bullets, not paragraphs
- Meeting note links in the daily note should use Obsidian wiki-link format: `[[Note Name]]`
- If no meeting notes are found for today via date search, that's fine — just omit that section
