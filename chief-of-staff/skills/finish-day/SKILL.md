---
name: finish-day
description: End-of-day wrap-up — reviews completed and incomplete Todoist tasks, triages the Todoist inbox, recaps today's calendar, reminds about transcripts (with optional n8n MCP trigger), reschedules incomplete tasks, preps tomorrow's meeting notes in Obsidian, and updates today's daily note with a day summary. Trigger when the user says "finish my day", "wrap up today", "end of day", or invokes /finish-day. Must be run from the root of the Obsidian vault.
argument-hint: '[--transcript-mcp <server-name>]'
---

# Finish Day

You are helping the user close out their workday. Review what was accomplished, handle transcripts, reschedule incomplete tasks, triage the inbox, prep tomorrow's meeting notes, and write an honest day summary.

## Vault Paths (relative to vault root)

- Daily notes: `02-AreasOfResponsibility/Daily Notes/`
- Meeting notes: `02-AreasOfResponsibility/Notes/`
- Projects: `01-Projects/` — each project has its own subfolder containing a `PLAN.md`

## Meeting Note Templates

When creating new meeting notes, read the appropriate template file and use it as the basis for the new note:

- **Recurring meeting:** [templates/recurring-meeting.md](templates/recurring-meeting.md)
- **Ad-hoc / one-off meeting:** [templates/adhoc-meeting.md](templates/adhoc-meeting.md)

---

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

**Inbox tasks:** Call `get_tasks` filtered to project `#Inbox` (or the inbox project ID). Capture all tasks regardless of due date.

**Today's calendar:** Call `list-events` on the Google Calendar MCP server for today.

**Today's daily note:** Check for and read `02-AreasOfResponsibility/Daily Notes/TODAY.md` using the Read tool if it exists.

**Gmail — priority emails:** Call the Gmail MCP server to search for unread emails with high-priority labels. Use the query:

```
label:Priority/p1 OR label:Priority/p2
```

(Adjust the exact tool name to match your Gmail MCP server.) For each email capture: subject, sender, date received, and any visible snippet or body. If unavailable, skip and note it.

If any MCP server is unavailable, tell the user which one and continue with whatever data is accessible.

## Phase 2: Surface Priority Emails

If any Priority/p1 or Priority/p2 emails were found, present them before the brain dump:

---

**Priority Emails Needing Your Attention**

For each email, one compact entry:

- **[Subject]** — from [Sender] · [Received]
  [1–2 sentence summary]
  **Action needed:** [Concrete decision or task the user is responsible for]

List p1 emails first. Ask: "Do any of these need a Todoist task created?" If yes, create them in `#Inbox` via `create_task` and confirm.

---

If no priority emails were found, skip this section entirely.

## Phase 3: Brain Dump

Before moving on, ask the user to do a quick brain dump:

> "Before we close out — what's still rattling around in your head that isn't captured yet? Any tasks, ideas, follow-ups, or things you promised someone today?"

Accept free-form input. For each item mentioned:

- Create it as a Todoist task in `#Inbox` via `create_task` (no due date, no project — inbox triage will handle it in Phase 5)
- Confirm what was captured: "Added to inbox: [task names]"

If the user says nothing or skips, move on. Don't force it.

## Phase 4: Day Review

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

## Phase 5: Transcript Reminder

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

## Phase 6: Reschedule Incomplete Tasks

Skip this phase if there are no incomplete tasks.

Present all incomplete tasks at once and ask the user what to do with each:

- **Tomorrow** — update due date to TOMORROW via `update_task`
- **Later this week** — ask for specific day
- **Next week** — update to next Monday
- **Deprioritize** — set no due date or lower priority
- **Done / Cancel** — mark complete via `complete_task`

Collect all decisions first, then execute all updates together in one batch.

## Phase 7: Inbox Triage

Skip this phase if there are no tasks in #Inbox.

Present all inbox tasks grouped by any obvious themes. For each task, ask the user:

- **Move to project** — which project? Update via `update_task` to move it and optionally set a due date
- **Schedule it** — stay in inbox but assign a due date
- **Delete / Cancel** — mark complete or delete via `delete_task`

Present all inbox tasks at once and collect all decisions before executing. Batch all Todoist updates together. The goal is zero inbox by the end of this phase — prompt the user if they're leaving tasks unactioned.

## Phase 8: Prep Tomorrow's Meeting Notes

This is what enables `/start-day` to find relevant meeting notes via date-string search tomorrow morning.

1. Call `list-events` for TOMORROW to get tomorrow's calendar events.

2. For each calendar event:

   **a. Determine if it's recurring or ad-hoc.**

   Check in order:
   1. **Calendar recurrence** — if the `list-events` response includes a recurrence rule or marks the event as recurring, it's recurring.
   2. **Existing note file** — use Glob to search `02-AreasOfResponsibility/Notes/` for a file matching the pattern `<meeting name>*.md` or `<person name>*.md` (e.g., `1:1 with Alex - 2026.md`). A year-suffixed filename is a strong signal of a recurring note.
   3. **Ask the user** — if neither signal is available: "Is '[Meeting Name]' a recurring meeting or a one-off?"

   **b. For recurring meetings with an existing note:**
   - Read the last date-stamped section of the note file to extract context (prior agenda items, open action items in the "Carried Forward" section).
   - Look for associated project docs in `01-Projects/`: use Glob to find folders whose name relates to the meeting topic, then read the `PLAN.md` inside. Surface any open action items or upcoming milestones that are relevant to this meeting. If nothing obvious matches, ask the user: "Are there any projects under `01-Projects/` I should pull context from for '[Meeting Name]'?"
   - Append a new section to the end of the file using Template A's date section stub, pre-populating the Agenda with any carried-forward items or relevant project context:

   ```markdown
   ## TOMORROW

   ### Agenda

   [Carried-forward items or open project tasks, if any]

   ### Notes

   ### Action Items

   - [ ]

   ### Carried Forward
   ```

   Replace `TOMORROW` with the actual date string (e.g., `## 2026-03-31`).

   **c. For ad-hoc meetings or recurring meetings without an existing note:**
   - If no note exists, ask the user: "I don't see a note for '[Meeting Name]'. Want me to create one?"
   - Also look for related project docs in `01-Projects/` and ask: "I found `01-Projects/[Project Name]/PLAN.md` — should I pull context from it?" If nothing matches, ask: "Are there any projects under `01-Projects/` I should pull context from?"
   - If the user confirms creation, use the Write tool to create `02-AreasOfResponsibility/Notes/<Meeting Name>.md` using:
     - **Template A** (Recurring) if it's a recurring meeting, with the first date section pre-populated
     - **Template B** (Ad-hoc) if it's a one-off, with DATE filled in as TOMORROW

   **d. All meetings get a note.** If a meeting has no note and the user declines to create one, note it explicitly: "Skipped note for '[Meeting Name]' — you'll need to create it manually if needed."

3. Tell the user which notes were updated or created: "Prepped sections in: [[1:1 with Alex]], [[Team Standup]]. Created new note: [[Product Review 2026-03-31]]."

## Phase 9: Tomorrow Preview (optional)

Ask: "Want a quick look at what's lined up for tomorrow?"

If yes, present:

- Tomorrow's calendar events (already fetched in Phase 5)
- Todoist tasks due tomorrow (call `get_tasks` filtered to TOMORROW)

Keep it brief — this is a preview, not a full briefing.

## Phase 10: Update Today's Daily Note

Use the Edit tool to append an "End of Day" section to `02-AreasOfResponsibility/Daily Notes/TODAY.md`. If no daily note exists, use the Write tool to create a minimal one.

Section to append:

```markdown
## End of Day

_Completed by /finish-day_

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
- Brain dump (Phase 1b) is intentionally low-friction — don't over-structure it, just capture what the user says
- Inbox triage (Phase 5) should aim for zero inbox — gently push back if the user wants to leave tasks unaddressed
- Meeting note prep (Phase 6) is the most important step for enabling tomorrow's start-day flow; don't skip it
- Every meeting on tomorrow's calendar should have a note — either existing (with a new section appended) or newly created
- The transcript reminder (Phase 3) must always be shown
- Batch all Todoist updates — don't send them one at a time while the user is still deciding
- When pulling context for recurring meetings, only surface items that are genuinely actionable — don't dump the entire note history
