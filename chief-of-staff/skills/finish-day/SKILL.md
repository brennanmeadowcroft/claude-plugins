---
name: finish-day
description: End-of-day wrap-up — reviews completed and incomplete Todoist tasks, triages the Todoist inbox, recaps today's calendar and Slack activity, reminds about transcripts (with optional n8n MCP trigger), reschedules incomplete tasks, preps tomorrow's meeting notes in Obsidian, and updates today's daily note with a day summary. Trigger when the user says "finish my day", "wrap up today", "end of day", or invokes /finish-day. Must be run from the root of the Obsidian vault.
---

# Finish Day

You are helping the user close out their workday. Review what was accomplished, handle transcripts, reschedule incomplete tasks, triage the inbox, prep tomorrow's meeting notes, and write an honest day summary.

## Arguments

- `--daily-notes-path <path>` — override daily notes folder (default: `02-AreasOfResponsibility/Daily Notes`)
- `--notes-path <path>` — override meeting notes folder (default: `02-AreasOfResponsibility/Notes`)

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
```

## Vault Paths (relative to vault root)

- Daily notes: resolved `daily-notes-path` (default: `02-AreasOfResponsibility/Daily Notes/`)
- Meeting notes: resolved `notes-path` (default: `02-AreasOfResponsibility/Notes/`)
- Projects: `01-Projects/` — each project has its own subfolder containing a `PLAN.md`

## Meeting Note Templates

When creating new meeting notes, read the appropriate template file and use it as the basis for the new note:

- **Recurring meeting:** [templates/recurring-meeting.md](templates/recurring-meeting.md)
- **Ad-hoc / one-off meeting:** [templates/adhoc-meeting.md](templates/adhoc-meeting.md)

---

## Phase 0: Get Today's and Tomorrow's Dates

**First, resolve vault paths.** Check `CLAUDE.md` at vault root for a "Chief of Staff" section and read `daily-notes-path` and `notes-path` values if present. Per-invocation arguments override CLAUDE.md values; CLAUDE.md values override hardcoded defaults. Use the resolved paths everywhere below.

Run via Bash:

```bash
echo "TODAY=$(date +%Y-%m-%d)"
echo "TOMORROW=$(date -v+1d +%Y-%m-%d 2>/dev/null || date -d tomorrow +%Y-%m-%d)"
```

Store TODAY and TOMORROW.

## Phase 1: Gather Today's Data

Run in parallel:

**Completed tasks:** Call `find-completed-tasks` filtered to today. Capture task name and project.

**Still-open tasks:** Call `find-tasks` filtered to due today and overdue. These are tasks that weren't finished.

**Inbox tasks:** Call `find-tasks` filtered to project `#Inbox` (or the inbox project ID). Capture all tasks regardless of due date.

**Today's calendar:** Call `list-events` on the Google Calendar MCP server for today.

Events with titles starting with `[IT]` are intentional focus time blocks scheduled by `/start-week`. When summarizing calendar activity in Phase 4, label them as focus blocks, not meetings.

**Today's daily note:** Check for and read `02-AreasOfResponsibility/Daily Notes/TODAY.md` using the Read tool if it exists.

**Gmail — priority emails:** Call the Gmail MCP server to search for unread emails with high-priority labels. Use the query:

```
label:Priority/p1 OR label:Priority/p2
```

(Adjust the exact tool name to match your Gmail MCP server.) For each email capture: subject, sender, date received, and any visible snippet or body. If unavailable, skip and note it.

**Slack — today's activity:** Call the Slack MCP server to retrieve messages from today. Fetch in this order:

1. **Direct messages** — conversations you sent or received today
2. **Mentions** — any messages where you were @-mentioned in any channel
3. **Active channels** — messages you posted in today

For each Slack item capture: channel or DM partner, timestamp, and a brief summary of the content. Focus on messages that indicate decisions made, commitments given, or action items promised. If the Slack MCP is unavailable, skip and note it.

If any MCP server is unavailable, tell the user which one and continue with whatever data is accessible.

## Phase 2: Surface Priority Emails

If any Priority/p1 or Priority/p2 emails were found, present them before the brain dump:

---

**Priority Emails Needing Your Attention**

For each email, one compact entry:

- **[Subject]** — from [Sender] · [Received]
  [1–2 sentence summary]
  **Action needed:** [Concrete decision or task the user is responsible for]

List p1 emails first. Ask: "Do any of these need a Todoist task created?" If yes, for each email the user wants to convert:

1. Create a 1–2 sentence task description explaining the intent (what the user needs to do and why, derived from the email content).
2. Include a Gmail link in the task description using the format `https://mail.google.com/mail/u/0/#inbox/MESSAGE_ID` where `MESSAGE_ID` is the email's message ID (request this from the Gmail MCP if available; if unavailable, note in the task that the email can be found by searching for the subject).
3. Create the task in `#Inbox` via `add-tasks` with the description and link included.
4. If the action needed is a decision, approval, or response that someone else is waiting on — i.e., the user is the blocker — add the label `@Process_Task` to the task.

Confirm all created tasks.

---

If no priority emails were found, skip this section entirely.

## Phase 3: Brain Dump

Before moving on, ask the user to do a quick brain dump:

> "Before we close out — what's still rattling around in your head that isn't captured yet? Any tasks, ideas, follow-ups, or things you promised someone today?"

Accept free-form input. For each item mentioned:

- Create it as a Todoist task in `#Inbox` via `add-tasks` (no due date, no project — inbox triage will handle it in Phase 5)
- If any item is framed as owing someone a decision, response, or approval (e.g., "I need to get back to X about Y", "I owe Z an answer on…"), add the label `@Process_Task` when creating that task.
- Confirm what was captured: "Added to inbox: [task names]"

If the user says nothing or skips, move on. Don't force it.

## Phase 3.5: Delegation Review

After the brain dump, look across what was gathered in Phases 1–3 and identify items suitable for background delegation via exec-monitor. These are **bucket-2 items** — work the EA can do while you review the result, not work that requires your judgment upfront.

**Delegation candidates to surface:**

- p1/p2 emails requiring a draft response (e.g., meeting reschedule requests, intro requests, status update replies, routine follow-ups where the content is clear from context)
- Slack commitments where you owe someone a response and the drafting is the main work
- Inbox tasks from the brain dump that are clearly "draft and send" in nature

**Do NOT flag** for delegation: anything requiring strategic judgment, sensitive relationship dynamics, decisions only you can make, or creative work where you haven't yet determined the direction.

If there are delegation candidates, surface them as a short list:

> "These look like good candidates to route to the EA for drafting — you'd review the draft before it goes:
>
> 1. **Draft reply to [Sender] re: [Subject]** — [1-sentence context]
> 2. **Draft follow-up to [Person] on [topic]** — [1-sentence context]
>
> Route them? [Yes, all] [Review each] [Skip]"

For each item the user approves, create a Todoist task in `#Inbox` with:
- **Title:** "Draft [action] — [Sender/Person] re: [topic]"
- **Label:** `@claude` (so exec-monitor picks it up automatically)
- **Description:** Include the email link (`https://mail.google.com/mail/u/0/#inbox/MESSAGE_ID` or search query), the desired action, and any relevant context (tone, key points to include). The more context, the better the draft.

Confirm which tasks were created: "Queued for exec-monitor: [task names]. They'll be picked up on the next run."

If nothing qualifies, skip this phase entirely — don't force it.

---

## Phase 4: Day Review

Present a brief, honest review:

---

**What You Accomplished**

- Completed Todoist tasks (with project)
- Calendar events that happened today

If any `[IT]` focus blocks were on today's calendar, note whether they were used productively (i.e., was related work completed?). This helps the user reflect on whether the focus blocking strategy is working.

**Slack Activity** (only if Slack data was retrieved)

Summarize today's Slack conversations to help jog memory. Group by type:

- _Decisions made_ — threads or DMs where a clear decision or direction was agreed upon
- _Commitments given_ — things you said you'd do, or that someone said they'd do for you
- _Notable conversations_ — anything substantive that doesn't fit the above

Keep each entry to one line. Present all Slack items at once and ask: "Do any of these need a task created?" If yes, for each item the user wants to convert:

1. Create a task in `#Inbox` via `add-tasks` with a 1–2 sentence description explaining the commitment or action item.
2. Include the Slack message link in the task description. Request a permalink from the Slack MCP (format: the direct link to the message/thread), or if unavailable, note the channel and timestamp so the user can find it.
3. If the Slack thread represents a commitment where Brennan owes someone a decision or response — i.e., someone else is waiting on him — add the label `@Process_Task` to the task.
4. Wait for the user's decision on each flagged item before proceeding to the next phase.

Confirm all created tasks.

**Still Open**

- Incomplete tasks with their original due date

**Day Patterns** (only if notable)
A p1 task finished, a project milestone hit, or a day that ran particularly long on meetings.

---

## Phase 5: Process Transcripts

Run the `/exec-assistant:process-transcripts` skill for today's meetings. Today's calendar events were already fetched in Phase 1 — pass that context so the skill does not need to re-fetch the calendar.

The skill will:
- Check `~/Nextcloud/Meeting Uploads/TODAY/` for transcript files matching today's meetings
- Generate structured summaries and write them into the appropriate Obsidian notes
- Create Todoist tasks in #Inbox for any action items

After the skill completes (or if the user skips), continue to Phase 6.

## Phase 6: Reschedule Incomplete Tasks

Skip this phase if there are no incomplete tasks.

Present all incomplete tasks at once and ask the user what to do with each:

- **Tomorrow** — update due date to TOMORROW via `update-tasks`
- **Later this week** — ask for specific day
- **Next week** — update to next Monday
- **Deprioritize** — set no due date or lower priority
- **Done / Cancel** — mark complete via `complete-tasks`

Collect all decisions first, then execute all updates together in one batch.

## Phase 7: Inbox Triage

Skip this phase if there are no tasks in #Inbox.

Present all inbox tasks grouped by any obvious themes. For each task, ask the user:

- **Move to project** — which project? Update via `update-tasks` to move it and optionally set a due date
- **Schedule it** — stay in inbox but assign a due date
- **Delete / Cancel** — mark complete via `complete-tasks` or delete via `delete-object`

Present all inbox tasks at once and collect all decisions before executing. Batch all Todoist updates together. The goal is zero inbox by the end of this phase — prompt the user if they're leaving tasks unactioned.

## Phase 8: Prep Tomorrow's Meeting Notes

This is what enables `/start-day` to find relevant meeting notes via date-string search tomorrow morning.

1. Call `list-events` for TOMORROW to get tomorrow's calendar events.

2. For each calendar event, use the /exec-assistant:meeting-prep skill to prep the notes. Provide the meeting name and the meeting date.

   **d. All meetings get a note.** If a meeting has no note and the user declines to create one, note it explicitly: "Skipped note for '[Meeting Name]' — you'll need to create it manually if needed."

3. Tell the user which notes were updated or created: "Prepped sections in: [[1:1 with Alex]], [[Team Standup]]. Created new note: [[Product Review 2026-03-31]]."

## Phase 9: Tomorrow Preview (optional)

Ask: "Want a quick look at what's lined up for tomorrow?"

If yes, present:

- Tomorrow's calendar events (already fetched in Phase 5)
- Todoist tasks due tomorrow (call `find-tasks` filtered to TOMORROW)

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
- When creating tasks from emails or Slack threads, always include both a meaningful description (intent and context) and a navigable link back to the source — this ensures the user can revisit the original message without friction
- Slack threads with open commitments should never be silently dropped — always surface them during the Slack Activity section and wait for explicit user input on whether each should become a task
