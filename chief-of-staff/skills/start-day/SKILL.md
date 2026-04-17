---
name: start-day
description: Morning briefing — pulls today's Google Calendar events, Todoist tasks, Gmail priority emails, weekly priorities, and meeting notes, then synthesizes a prioritized daily plan. Optionally creates today's daily note. Trigger when the user says "start my day", "morning briefing", or invokes /start-day. Must be run from the root of the Obsidian vault.
---

# Start Day

You are helping the user plan their day. Pull data from their calendar, task manager, email, and vault, and synthesize a clear morning briefing.

## Arguments

- `--daily-notes-path <path>` — override daily notes folder (default: `02-AreasOfResponsibility/Daily Notes`)
- `--notes-path <path>` — override meeting notes folder (default: `02-AreasOfResponsibility/Notes`)
- `--weekly-recaps-path <path>` — override weekly recaps folder (default: `02-AreasOfResponsibility/Weekly Recaps`)

## Configuration

If a `CLAUDE.md` exists at the vault root with a **Chief of Staff** config block, path values there are used as defaults — no arguments needed. The precedence for each path is:

1. Per-invocation argument (highest)
2. Value from `CLAUDE.md` Chief of Staff block
3. Hardcoded default

Example `CLAUDE.md` block:

```
## Chief of Staff
- daily-notes-path: Journal/Daily
- notes-path: Meetings
- weekly-recaps-path: Reviews/Weekly
```

## Vault Paths (relative to vault root)

- Daily notes: resolved `daily-notes-path` (default: `02-AreasOfResponsibility/Daily Notes/`)
- Meeting notes: resolved `notes-path` (default: `02-AreasOfResponsibility/Notes/`)
- Weekly recaps: resolved `weekly-recaps-path` (default: `02-AreasOfResponsibility/Weekly Recaps/`)

## Phase 0: Get Today's Date

**First, resolve vault paths.** Check `CLAUDE.md` at vault root for a "Chief of Staff" section and read `daily-notes-path`, `notes-path`, and `weekly-recaps-path` values if present. Per-invocation arguments override CLAUDE.md values; CLAUDE.md values override hardcoded defaults. Use the resolved paths everywhere below.

Run via Bash:
```bash
TODAY=$(date +%Y-%m-%d)
DAY_NAME=$(date +%A)
DOW=$(date +%u)
WEEK_START=$(date -v-$((DOW - 1))d +%Y-%m-%d 2>/dev/null || date -d "$(date +%Y-%m-%d) -$(($(date +%u)-1)) days" +%Y-%m-%d)
WEEK_NUM=$(date +%Y-W%V)
echo "TODAY=$TODAY DAY_NAME=$DAY_NAME WEEK_START=$WEEK_START WEEK_NUM=$WEEK_NUM"
```

Store TODAY, DAY_NAME, WEEK_START, and WEEK_NUM.

## Phase 1: Gather Today's Data

Run all of these in parallel:

**Calendar:** Call `list-events` on the Google Calendar MCP server for today (midnight to midnight). For each event capture: title, start/end time, attendees, video call link if present. If unavailable, tell the user and ask them to describe their schedule manually.

**Todoist — due today:** Call `find-tasks` filtered to tasks due today. For each task capture: name, project, priority (p1–p4), any due time. If Todoist MCP is unavailable, tell the user and continue without task data.

**Todoist — overdue:** Call `find-tasks` filtered to overdue tasks. Note how many days overdue each task is.

**Todoist — process tasks:** Call `find-tasks` filtered to label `@Process_Task`. Capture name, project, priority (p1–p4), and due date. These are tasks where someone is waiting on you for a decision, approval, or response.

**Gmail — priority emails:** Call the Gmail MCP server to search for unread emails with high-priority labels. Use the query:
```
label:Priority/p1 OR label:Priority/p2 is:unread
```
(Adjust the exact tool name and query format to match your Gmail MCP server. Common tool names: `search_emails`, `list_messages`, `query_emails`.) For each email capture: subject, sender, date received, and any visible snippet or body. If Gmail MCP is unavailable, skip and note it.

**Weekly priorities:** Attempt to read the current week's planning file:
```
02-AreasOfResponsibility/Weekly Recaps/WEEK_NUM.md
```
(Replace WEEK_NUM with the actual value, e.g., `2026-W14`.) If it exists, extract the "## Priorities This Week" section. If the file does not exist, the weekly priorities section in the briefing should be omitted — prompt the user to run `/start-week` if they haven't yet.

**Meeting notes for today:** Use Grep to search for notes containing today's date string in `02-AreasOfResponsibility/Notes/`. These are long-running meeting notes that have a section for today, added by `/finish-day` the previous evening. Read each matching file to get the section content.

**Existing daily note:** Check if today's daily note exists at `02-AreasOfResponsibility/Daily Notes/TODAY.md`. If it exists, read it.

## Phase 2: Synthesize Morning Briefing

Present the briefing in this structure:

---

### Good [morning/afternoon] — [DAY_NAME], [Full Date]

**At a Glance**
[X] calendar events · [Y] tasks due today · [Z] overdue · [N] priority emails · [P] process tasks

**Process Tasks** (omit section entirely if no @Process_Task tasks found)
These are items where someone is waiting on you — decisions, approvals, or responses. You have dedicated time set aside for these today.

For each task, one compact entry:
- **[Task name]** — [project] · [due date if set] · [priority if p1 or p2]

**Priority Emails** (omit section entirely if no p1/p2 emails found)
For each Priority/p1 or Priority/p2 email, one compact entry:
- **[Subject]** — from [Sender] · [Date]
  [1–2 sentence summary of content]
  **Action needed:** [What the user specifically needs to decide or do — be concrete]

List p1 emails first, then p2. If Gmail MCP was unavailable, note it briefly here.

**Weekly Priorities** (omit section if no weekly priorities were found)
Show the 2–3 priorities set in `/start-week` for this week. This gives daily context for task ranking.
- [Priority 1]
- [Priority 2]
- [Priority 3 if set]

**Calendar**
List events chronologically with start and end times. Flag any day with more than 4 hours of back-to-back meetings. Note if a meeting note was found for any event (e.g., `→ [[1:1 with Alex]]`).

Events with titles starting with `[IT]` are intentional focus time blocks, not meetings. In the calendar listing, label them as "Focus: [rest of title]" and note that they are schedulable if an important meeting needs to be placed there.

**Top Priorities**
Synthesize Todoist p1 and p2 tasks into a ranked list of 3–5 focus areas. Where relevant, note alignment with the weekly priorities above. Briefly explain the ranking (e.g., "p1, overdue 2 days"). Keep it scannable.

**Overdue Items**
List overdue tasks grouped by how long they've been overdue. Flag anything overdue more than 3 days.

**Suggested Focus Blocks** (only if there are clear calendar gaps)
Based on gaps between events, suggest 1–3 windows for deep work. Example: "9:00–11:00 — clear before standup, good for [top priority]."

If the user already has `[IT]` focus blocks scheduled, reference them here rather than suggesting new ones. Only suggest new windows if gaps exist beyond the scheduled focus blocks.

**Today's Meeting Notes**
If meeting notes were found for today, list the note title and any relevant content from the today section.

---

## Phase 3: Create Daily Note (optional)

Ask: "Would you like me to create today's daily note?"

If yes (and one doesn't already exist), use the Write tool to create `02-AreasOfResponsibility/Daily Notes/TODAY.md`:

```markdown
---
date: TODAY
tags: [daily-note]
---

# DAY_NAME, Full Date

## Morning Intentions

[Top 3 priorities from Phase 2]

## Schedule

[Calendar events, one per line with times]

## Meeting Notes

[Wiki-links to today's relevant meeting notes, e.g., [[1:1 with Alex]], [[Team Standup]]]

## Notes

## End of Day
<!-- Filled in by /finish-day -->
```

If a daily note already exists, use the Edit tool to add or update only the "Morning Intentions" section.

## Quality Notes

- Always use the date from Bash, never infer it
- Priorities should reflect both urgency (due dates, overdue status) and importance (Todoist priority levels)
- Keep the briefing scannable — headers and bullets, not paragraphs
- Meeting note wiki-links use Obsidian format: `[[Note Name]]`
- If no meeting notes are found for today, omit that section — it means `/finish-day` wasn't run last night
- @Process_Task items that are due today or overdue should also appear in "Top Priorities" — the Process Tasks section surfaces them as a group, but they still count toward urgency ranking
