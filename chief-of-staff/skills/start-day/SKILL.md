---
name: start-day
description: Morning briefing — pulls today's Google Calendar events, Todoist tasks, Gmail priority emails, weekly priorities, and meeting notes, then synthesizes a prioritized daily plan. Optionally creates today's daily note. Trigger when the user says "start my day", "morning briefing", or invokes /start-day. Must be run from the root of the Obsidian vault.
---

# Start Day

You are helping the user plan their day. Pull data from their calendar, task manager, email, and vault, and synthesize a clear morning briefing.

## Vault Paths (relative to vault root)

- Daily notes: `02-AreasOfResponsibility/Daily Notes/`
- Meeting notes: `02-AreasOfResponsibility/Notes/`
- Weekly recaps: `02-AreasOfResponsibility/Weekly Recaps/`

## Phase 0: Get Today's Date

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
[X] calendar events · [Y] tasks due today · [Z] overdue · [N] priority emails

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

**Top Priorities**
Synthesize Todoist p1 and p2 tasks into a ranked list of 3–5 focus areas. Where relevant, note alignment with the weekly priorities above. Briefly explain the ranking (e.g., "p1, overdue 2 days"). Keep it scannable.

**Overdue Items**
List overdue tasks grouped by how long they've been overdue. Flag anything overdue more than 3 days.

**Suggested Focus Blocks** (only if there are clear calendar gaps)
Based on gaps between events, suggest 1–3 windows for deep work. Example: "9:00–11:00 — clear before standup, good for [top priority]."

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
