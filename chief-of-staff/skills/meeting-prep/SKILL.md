---
name: meeting-prep
description: Prepare for a meeting by gathering context from Google Calendar, Todoist tasks, project plans, existing Obsidian meeting notes, and user-provided notes, then generating a structured meeting note with classified agenda items. Trigger when the user says "prep for meeting", "prepare for a meeting", "meeting prep", "get ready for my meeting", "prep me for", or invokes /meeting-prep. Also trigger when the user mentions an upcoming meeting and wants to organize their talking points or agenda. Works for meetings on any date, not just today. Must be run from the root of the Obsidian vault.
---

# Meeting Prep

You are helping the user prepare for a meeting. Your job is to gather relevant context from multiple sources, distill it into a concise agenda, and write a meeting note they can reference during the conversation.

## Vault Paths (relative to vault root)

- Meeting notes: `02-AreasOfResponsibility/Notes/`
- Projects: `01-Projects/` — each project has its own subfolder containing a `PLAN.md`

## Phase 0: Identify the Meeting

Start by figuring out which meeting the user is preparing for. You need:

1. **Meeting name** — what the note file will be called
2. **What to pull from** — any combination of:
   - A Todoist project name (you'll search for it)
   - A Project PLAN.md path (you'll read it)
   - Free-form context the user pastes in (conversation notes, email threads, etc.)
3. **Who's in the meeting** — names for the Contacts field (Obsidian wiki-link format)

If the user refers to an attendee by first name or alias only (e.g., "meeting with Carolyn"), call `find_contact` with that name before searching the calendar. If a match is found, use the canonical full name and email for all subsequent lookups. If not found, proceed with the user's input as-is.

If the user already provided this information in their message, don't re-ask — just confirm what you understood and proceed. The user may not have all three; work with whatever they give you.

## Phase 1: Gather Context

Run these in parallel based on what's available:

### Google Calendar

Search for the meeting on Google Calendar using `gcal_list_events` with the `q` parameter set to the meeting name. Search a reasonable window — if the user said "tomorrow's standup," search tomorrow; if they just said the meeting name, search the next 7 days. Pick the nearest matching event.

If the first search returns no results, try broader or alternate terms. Meeting names in conversation often don't match the calendar event title exactly — e.g., the user might say "Q2 Planning" but the event is called "Q2 OKR Draft Review." Try dropping words, using key terms, or searching for the topic rather than the exact name. Make 2-3 attempts with different queries before giving up.

From the calendar event, extract:

- **Meeting date and time** — this becomes the MeetingDate in the note's frontmatter. The calendar is the authoritative source for the date.
- **Attendees** — use these for the Contacts field if the user didn't specify. After extracting attendees, call `lookup_contact` for each attendee email. If a match is found in your personal contacts, use the canonical `name` field for Obsidian `[[wiki links]]` and note any `team` or `notes` fields as context. If not found, use the display name from the calendar event as-is.
- **Description / notes link** — calendar events sometimes include a Google Docs link for meeting notes. If you find one, try to fetch its content using the appropriate MCP tool.
- **One time or recurring meeting** - this affects how you search for existing notes later. Recurring meetings often have a year-based note (e.g., "Standup - 2026.md") while one-time meetings typically have a single note named after the meeting (e.g., "Q2 Planning.md").
- **1:1 or group meeting** - this affects how you search for existing notes and Slack messages later. 1:1 meetings will typically be named after the two participants (e.g., "Brennan / Alice") while group meetings have more thematic names (e.g., "Product Sync").

If no calendar event is found, default the meeting date to today (get it from Bash: `date +%Y-%m-%d`).

### Existing Obsidian Meeting Note

Check for an existing recurring note. Recurring notes follow the naming pattern `{Meeting Name} - {YEAR}.md` (e.g., `Standup - 2026.md`). Use Glob to search:

```
02-AreasOfResponsibility/Notes/{meeting name}*.md
```

If the meeting is a one-on-one (e.g., "Brennan / Alice"), use the email of the other participant to (e.g. asmith@company.com) and check for the pattern `{First Name} {Last Name} - {Year}.md` (e.g., `Alice Smith - 2026.md`).

If a recurring note exists, read the most recent date section. Look for:

- Items under `### For Next Time` — these carry forward and belong in the new agenda
- Unresolved items from `### Their Topics` or `### My Topics` that seem ongoing
- Context about what was discussed last time that informs this meeting

### Todoist Tasks

If a project was referenced or has the existing meeting note has a tag, use `find-tasks` to fetch all open tasks. Use `responsibleUserFiltering: "all"` to include tasks assigned to anyone. If the project name doesn't match exactly, try `find-projects` to locate it.

### Slack

If available, search Slack for recent messages related to the meeting topic. Use `slack_search_messages` with the meeting name or key topic as the query. If it is a 1:1 meeting, search for messages in the DM channel with that person. Look for topics

### Project Plan

If a PLAN.md path was given, read it. Pay attention to:

- Open questions and assumptions (decision candidates)
- Unchecked tasks (pending work)
- Phase structure and exit criteria (what's blocking progress)

If it's a 1:1 meeting, use the /project-index skill to find projects of which the other participant is an owner or collaborator, then check those plans for relevant context.

### Gmail

Search Gmail for recent email threads related to the meeting topic. Use `gmail_search_messages` with the meeting name or key topic as the query. Look for:

- Pre-read materials or agendas sent by the organizer
- Email threads discussing the meeting topic that contain decisions, context, or action items
- Prep instructions (e.g., "please come prepared with your Q2 OKRs")

This is especially valuable when the user provides minimal context — email threads often contain the richest source of meeting background.

### Weekly Priorities

Check the current week's planning file at `02-AreasOfResponsibility/Weekly Recaps/` (the most recent `YYYY-WNN.md` file). If it exists, extract the priorities section. This provides context about what the user is focused on this week, which helps identify which agenda items matter most and surfaces relevant work that might not be in Todoist or the plan.

### User-Provided Context

Parse any notes, conversation excerpts, or bullet points the user provided. These often contain the most current information — things that haven't made it into Todoist or the plan yet.

## Phase 2: Classify Items

Go through every piece of information gathered and classify each item into one of four categories:

**Decision** — Something that needs to be decided in this meeting. Signals: open questions in the plan, items where multiple options exist and no one has chosen, items the user described as "need to decide" or "TBD." Decisions are the most valuable use of meeting time, so they get prominent placement.

**Status update** — Something actively in progress where the group just needs awareness. Signals: tasks with assignees and due dates, items the user described as "working on" or "in progress." Quick — one bullet, one sub-bullet of context.

**Pending work** — Implementation tasks that don't need individual meeting discussion but the group should know exist. Signals: unchecked tasks in the plan that aren't blocked by a decision, Todoist tasks with no particular urgency. These get rolled up under a parent bullet.

**Open question** — Strategic or process questions where the gap is acknowledged but there may not be a clear decision to make yet. Signals: "we don't know how to," "need to figure out," "no clear approach." Discussion starters at the end.

## Phase 3: Build the Agenda

Structure the agenda under `### My Topics` following these rules:

**Ordering:**

1. Status updates (quick, builds shared context for the decisions)
2. Decisions (the meat of the meeting)
3. Pending work (rolled up, informational)
4. Open questions (discussion starters at the end)

**Formatting:**

- Top-level bullet = short topic label, plain text, no bold or other markdown formatting
- Indented sub-bullet (one tab) = one sentence of context explaining why it matters or what the ask is
- Sub-sub-bullets (two tabs) for items grouped under a parent like "Work that is still pending"

**Grouping pending work:** If there are 3+ pending implementation tasks, roll them up under a single top-level bullet called "Work that is still pending" with each task as a sub-bullet. If there are only 1-2, they can stand alone.

**Carry-forward items:** If the previous meeting note had a `### For Next Time` section with items, include those in the agenda. They represent commitments or topics that were explicitly deferred.

**Keep it tight:** Each sub-bullet should be one sentence. The user will elaborate verbally — the note is a reference, not a script.

### Example output

```
### My Topics
- Security remediation
	- Findings are in hand. AI security findings and infrastructure findings being remediated today/this week.
- Domain decision needed
	- Need to decide on the URL for Chauncey for Brokers (e.g. SLA Chauncey URL). Blocks deployment.
- VRI — ship or flag off?
	- Patrick is building a model to support VRI. Do we like the current version enough to ship, or flag it off until the new model is ready?
- Pipeline decision — existing vs. parallel?
	- Does Chauncey for Brokers use Chauncey's existing submission pipeline or a parallel one? Affects monitoring, debugging, and operational complexity.
- Work that is still pending
	- Login functionality
		- Password reset and properly formatted login emails need to be implemented before external access.
	- Broker email reformat
		- Current email with chat history is a "dump." Needs restructuring into a professional format.
	- Underwriter contact info — in or out?
		- If in, need to decide where the data comes from and how it's surfaced.
- Eval approach
	- No clear methodology for evaluating AI quality (completeness check, appetite check, SBP check). Need to start thinking about what "good" looks like and who owns figuring this out.
```

## Phase 4: Write the Meeting Note

### Recurring meetings (existing year-based note found)

If a recurring note exists (e.g., `Standup - 2026.md`), insert a new date section at the **top** of the file, immediately after the YAML frontmatter closing `---`. The newest date section should always be first in the file. Use the Edit tool to insert before the first existing `## ` heading. The section should use the template from "./templates/recurring-meeting.md" with the date and agenda items filled in.

If a plan was referenced, add a _snake case_ tag of the project name to the frontmatter (e.g. "Policy Peer Review Skill" becomes "policy_peer_review_skill"). The project name is based on the project folder name or todoist project name; they are both named the same.

Replace `MEETING_DATE` with the date from the calendar event (or today if no event was found) in a YYYY-MM-DD format.

### New meetings (no existing note)

Create the file at `02-AreasOfResponsibility/Notes/{meeting name}.md` using the template from "./templates/adhoc-meeting.md" with the date and agenda items filled in.

Replace `MEETING_DATE` with the date from the calendar event (or today if no event was found) in a YYYY-MM-DD format.

If a plan was referenced, add a _snake case_ tag of the project name to the frontmatter (e.g. "Policy Peer Review Skill" becomes "policy_peer_review_skill"). The project name is based on the project folder name or todoist project name; they are both named the same.

### After writing

Tell the user the file path and give a brief summary: how many decisions, status updates, pending items, and open questions are in the agenda. Ask if they want to adjust anything before the meeting.

## Quality Notes

- The calendar event is the authoritative source for meeting date — only fall back to today if no event is found
- The agenda is a reference for the user to glance at during the meeting — keep bullets scannable
- Never fabricate agenda items. Every bullet must trace back to a real source — calendar, Todoist, the plan, the previous meeting note, Gmail, weekly priorities, or the user's context. If no sources yield agenda items, say so plainly: "I didn't find specific items for the agenda from your calendar, tasks, or email. What topics do you want to cover?" An empty agenda that prompts the user is far more useful than generic placeholders
- If the user provided context that contradicts or updates what's in Todoist/the plan, trust the user's context — it's more current
- Use tab characters (not spaces) for bullet indentation — this is an Obsidian vault and tabs render correctly in preview
- For recurring notes, always insert the new section at the top (after frontmatter) — never at the bottom
- Preserve all existing content in recurring notes — only insert, never modify or remove
