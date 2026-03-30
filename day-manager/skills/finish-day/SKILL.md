---
name: finish-day
description: End-of-day wrap-up — reviews completed and incomplete Todoist tasks, recaps today's calendar, reminds about transcripts (with optional n8n MCP trigger), reschedulesincomplete tasks, preps tomorrow's meeting notes in Obsidian, and updates today's daily note with a day summary. Trigger when the user says "finish my day", "wrap up today", "end of day", or invokes /finish-day.
argument-hint: "[--daily-notes-path <path>] [--notes-path <path>] [--transcript-mcp <server-name>]"
---

# Finish Day

You are helping the user close out their workday. Review what was accomplished, handle transcripts, reschedule incomplete tasks, prep tomorrow's meeting notes, and write an honest day summary.

Default paths (override with arguments):
- Daily notes: `Daily Notes/` (e.g., `Daily Notes/2026-03-30.md`)
- Meeting notes: `Notes/`

## Phase 0: Pre-Flight Check

1. Get today's date via Bash: `date +%Y-%m-%d`. Store as TODAY. Get tomorrow's date: `date -v+1d +%Y-%m-%d` (macOS) or `date -d tomorrow +%Y-%m-%d` (Linux). Store as TOMORROW.
2. Verify all three MCP servers (Todoist, Google Calendar, Obsidian) are reachable with lightweight calls.
3. If any server fails, STOP and tell the user which one is unreachable with the fix command from the README.

## Phase 1: Gather Today's Data

Run in parallel:

**Completed tasks:** Call `get_completed_tasks` filtered to today. Capture task name and project.

**Still-open tasks:** Call `get_tasks` filtered to due today and overdue. These are tasks that weren't finished.

**Today's calendar:** Call `list-events` for today. This is the record of what meetings/calls actually happened.

**Today's daily note:** Attempt `read_note` on `<daily-notes-path>/TODAY.md`. Read it if it exists — provides morning context.

## Phase 2: Day Review

Present a brief, honest review:

---

**What You Accomplished**
- Completed Todoist tasks (with project)
- Calendar events that happened today (meetings, calls)

**Still Open**
- Incomplete tasks with their original due date

**Day Patterns** (include if notable)
Note anything worth acknowledging: a p1 task finished, a project milestone hit, or a day that ran long on meetings.

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

*If `--transcript-mcp <server-name>` was passed and that MCP server is available:*
> I see the `<server-name>` MCP server is configured. Would you like me to trigger transcript processing now? Tell me which tool to call and I'll run it.
> Then call the tool the user specifies on that server.

*If no transcript MCP is configured:*
> To automate this in the future, expose your n8n webhook as an MCP server and pass `--transcript-mcp <server-name>` to this skill. See the README for details.

---

Options for the user:
1. **Done** — transcripts are handled
2. **Skip** — no transcripts today
3. **Remind me later** — note it in the daily note

## Phase 4: Reschedule Incomplete Tasks

If there are no incomplete tasks, skip this phase.

Present all incomplete tasks at once and ask the user what to do with each:
- **Tomorrow** — update due date to TOMORROW via `update_task`
- **Later this week** — ask for specific day
- **Next week** — update to next Monday
- **Deprioritize** — set no due date or lower priority
- **Done / Cancel** — mark complete via `complete_task`

Collect all decisions first, then execute all `update_task` and `complete_task` calls together in one batch.

## Phase 5: Prep Tomorrow's Meeting Notes

This is what enables `/start-day` to find relevant meeting notes via date-string search tomorrow morning.

1. Call `list-events` for TOMORROW to get tomorrow's calendar events.
2. For each named recurring meeting (skip one-offs that don't have a corresponding note):
   a. Call `search_notes` with the meeting title as the query to find the long-running note in `Notes/`
   b. If a note is found with a confidence match: call `patch_note` to append this section to the end of the note:

```markdown

## TOMORROW

### Agenda

### Notes

```

   Replace `TOMORROW` with the actual date string (e.g., `## 2026-03-31`).

   c. If no matching note is found: ask the user — "I don't see a note for '[Meeting Name]'. Want me to create one in Notes/?"
   d. If the user confirms, use `write_note` to create `Notes/<Meeting Name>.md` with the section stub.

3. Tell the user which notes were updated: "Prepped sections in: [[1:1 with Alex]], [[Team Standup]]"

## Phase 6: Tomorrow Preview (optional)

Ask: "Want a quick look at what's lined up for tomorrow?"

If yes, present:
- Tomorrow's calendar events (already fetched in Phase 5)
- Todoist tasks due tomorrow (call `get_tasks` filtered to TOMORROW)

Keep it brief — this is a preview, not a full briefing.

## Phase 7: Update Today's Daily Note

Use `patch_note` to append an "End of Day" section to today's daily note. If no daily note exists, use `write_note` to create a minimal one.

The section to append:

```markdown

## End of Day
*Completed by /finish-day*

### Accomplished
[Completed tasks and notable meetings]

### Carried Forward
[Rescheduled tasks and where they went — e.g., "Fix auth bug → tomorrow", "Update docs → deprioritized"]

### Reflection
[Ask the user: "Any reflections on today you'd like to capture?" Then write their response here, or leave a placeholder if they skip.]
```

Ask before writing the reflection: "Any thoughts on today to capture in your notes?" Include their response verbatim (or "—" if they skip).

## Quality Notes

- The day review should be honest — acknowledge what didn't happen without judgment
- Meeting note prep (Phase 5) is the most important step for enabling tomorrow's start-day flow; don't skip it
- The transcript reminder (Phase 3) must always be shown, even if brief
- Batch all Todoist updates — don't call `update_task` one at a time while the user is still deciding
