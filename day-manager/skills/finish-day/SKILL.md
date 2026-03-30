---
name: finish-day
description: End-of-day wrap-up — reviews completed and incomplete Todoist tasks, recaps today's calendar, reminds about transcripts (with optional n8n MCP trigger), reschedules incomplete tasks, preps tomorrow's meeting notes in Obsidian, and updates today's daily note with a day summary. Trigger when the user says "finish my day", "wrap up today", "end of day", or invokes /finish-day. Must be run from the root of the Obsidian vault.
argument-hint: "[--transcript-mcp <server-name>]"
---

# Finish Day

You are helping the user close out their workday. Review what was accomplished, handle transcripts, reschedule incomplete tasks, prep tomorrow's meeting notes, and write an honest day summary.

## Vault Paths (relative to vault root)

- Daily notes: `02-AreasOfResponsibility/Daily Notes/`
- Meeting notes: `02-AreasOfResponsibility/Notes/`

## Phase 0: Get Today's and Tomorrow's Dates

Run via Bash:
```bash
echo "TODAY=$(date +%Y-%m-%d)"
echo "TOMORROW=$(date -v+1d +%Y-%m-%d 2>/dev/null || date -d tomorrow +%Y-%m-%d)"
```

Store TODAY and TOMORROW.

## Phase 1: Gather Today's Data

Run in parallel:

**Completed tasks:** Call `get_completed_tasks` on the Todoist MCP server filtered to today. Capture task name and project.

**Still-open tasks:** Call `get_tasks` filtered to due today and overdue. These are tasks that weren't finished.

**Today's calendar:** Call `list-events` on the Google Calendar MCP server for today.

**Today's daily note:** Check for and read `02-AreasOfResponsibility/Daily Notes/TODAY.md` using the Read tool if it exists.

If either MCP server is unavailable, tell the user which one and continue with whatever data is accessible.

## Phase 2: Day Review

Present a brief, honest review:

---

**What You Accomplished**
- Completed Todoist tasks (with project)
- Calendar events that happened today

**Still Open**
- Incomplete tasks with their original due date

**Day Patterns** (only if notable)
A p1 task finished, a project milestone hit, or a day that ran particularly long on meetings.

---

## Phase 3: Transcript Reminder

ALWAYS present this step. Never skip it.

---

**Transcript Upload**

If you recorded any meetings or conversations today, now is the time to download and save them to your n8n pickup folder.

```
[ ] Downloaded all transcripts from your recording tool
[ ] Saved to n8n pickup folder
```

If `--transcript-mcp <server-name>` was passed and that MCP server is available:
> I see the `<server-name>` MCP server is configured. Would you like me to trigger transcript processing now? Tell me which tool to call and I'll run it. Then call whatever tool the user specifies.

If no transcript MCP is configured:
> To automate this in the future, expose your n8n webhook as an MCP server and pass `--transcript-mcp <server-name>` to this skill.

---

Options:
1. **Done** — transcripts are handled
2. **Skip** — no transcripts today
3. **Remind me later** — note it in the daily note

## Phase 4: Reschedule Incomplete Tasks

Skip this phase if there are no incomplete tasks.

Present all incomplete tasks at once and ask the user what to do with each:
- **Tomorrow** — update due date to TOMORROW via `update_task`
- **Later this week** — ask for specific day
- **Next week** — update to next Monday
- **Deprioritize** — set no due date or lower priority
- **Done / Cancel** — mark complete via `complete_task`

Collect all decisions first, then execute all updates together in one batch.

## Phase 5: Prep Tomorrow's Meeting Notes

This is what enables `/start-day` to find relevant meeting notes via date-string search tomorrow morning.

1. Call `list-events` for TOMORROW to get tomorrow's calendar events.
2. For each named recurring meeting (skip one-offs that clearly won't have a note):
   a. Search for a matching note file using Glob: `02-AreasOfResponsibility/Notes/*.md`, then look for a filename that closely matches the meeting title.
   b. If a matching note is found, use the Edit tool to append this section to the end of the file:

```markdown

## TOMORROW

### Agenda

### Notes

```

   Replace `TOMORROW` with the actual date string (e.g., `## 2026-03-31`).

   c. If no matching note is found, ask the user: "I don't see a note for '[Meeting Name]'. Want me to create one?"
   d. If confirmed, use the Write tool to create `02-AreasOfResponsibility/Notes/<Meeting Name>.md` with the section stub above.

3. Tell the user which notes were updated: "Prepped sections in: [[1:1 with Alex]], [[Team Standup]]"

## Phase 6: Tomorrow Preview (optional)

Ask: "Want a quick look at what's lined up for tomorrow?"

If yes, present:
- Tomorrow's calendar events (already fetched in Phase 5)
- Todoist tasks due tomorrow (call `get_tasks` filtered to TOMORROW)

Keep it brief — this is a preview, not a full briefing.

## Phase 7: Update Today's Daily Note

Use the Edit tool to append an "End of Day" section to `02-AreasOfResponsibility/Daily Notes/TODAY.md`. If no daily note exists, use the Write tool to create a minimal one.

Section to append:

```markdown

## End of Day
*Completed by /finish-day*

### Accomplished
[Completed tasks and notable meetings]

### Carried Forward
[Rescheduled tasks and where they went — e.g., "Fix auth bug → tomorrow", "Update docs → deprioritized"]

### Reflection
[User's response to: "Any thoughts on today to capture in your notes?" — or "—" if skipped]
```

Ask before writing: "Any thoughts on today to capture in your notes?" Include their response verbatim, or "—" if they skip.

## Quality Notes

- The day review should be honest — acknowledge what didn't happen without judgment
- Meeting note prep (Phase 5) is the most important step for enabling tomorrow's start-day flow; don't skip it
- The transcript reminder (Phase 3) must always be shown
- Batch all Todoist updates — don't send them one at a time while the user is still deciding
