---
name: meeting-prep
description: Prepare for a meeting by gathering context from Google Calendar, Todoist tasks, project plans, existing Obsidian meeting notes, and user-provided notes, then generating a structured meeting note with classified agenda items. Trigger when the user says "prep for meeting", "prepare for a meeting", "meeting prep", "get ready for my meeting", "prep me for", or invokes /meeting-prep. Also trigger when the user mentions an upcoming meeting and wants to organize their talking points or agenda. Works for meetings on any date, not just today. Must be run from the root of the Obsidian vault.
---

# Meeting Prep

You are helping the user prepare for a meeting. Your job is to gather relevant context from multiple sources, distill it into a concise agenda, and write a meeting note they can reference during the conversation.

## Arguments

- `--notes-path <path>` — override meeting notes folder (default: `02-AreasOfResponsibility/Notes`)
- `--projects-path <path>` — override projects folder (default: `01-Projects`)

## Configuration

If a `CLAUDE.md` exists at the vault root with a **Chief of Staff** config block, path values there are used as defaults — no arguments needed. The precedence for each path is:

1. Per-invocation argument (highest)
2. Value from `CLAUDE.md` Chief of Staff block
3. Hardcoded default

Example `CLAUDE.md` block:

```
## Chief of Staff
- notes-path: Meetings
- projects-path: Projects
```

## Vault Paths (relative to vault root)

- Meeting notes: resolved `notes-path` (default: `02-AreasOfResponsibility/Notes/`)
- Projects: resolved `projects-path` (default: `01-Projects/`) — each project has its own subfolder containing a `PLAN.md`

## Phase 0: Identify the Meeting

**First, resolve vault paths.** Check `CLAUDE.md` at vault root for a "Chief of Staff" section and read `notes-path` and `projects-path` values if present. Per-invocation arguments override CLAUDE.md values; CLAUDE.md values override hardcoded defaults. Use the resolved paths everywhere below.

Start by figuring out which meeting the user is preparing for. You need:

1. **Meeting name** — what the note file will be called
2. **What to pull from** — any combination of:
   - A Todoist project name (you'll search for it)
   - A Project PLAN.md path (you'll read it)
   - Free-form context the user pastes in (conversation notes, email threads, etc.)
3. **Who's in the meeting** — names for the Contacts field (Obsidian wiki-link format)

If the user refers to an attendee by first name or alias only (e.g., "meeting with Carolyn"), call `find_contact` with that name before searching the calendar. If a match is found, use the canonical full name and email for all subsequent lookups. If not found, proceed with the user's input as-is.

After resolving the attendee contact, check whether the returned contact object has `is_direct_report: true`. Set an `is_direct_report` flag for use in Phase 1 and Phase 3. If no contact was found or the field is absent, treat it as false.

**Example `contacts.yaml` entry for a direct report:**
```yaml
- name: "Alice Smith"
  email: "alice@company.com"
  is_direct_report: true
```

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

If it's a 1:1 meeting, use the /project-manager:project-index skill to find projects of which the other participant is an owner or collaborator, then check those plans for relevant context.

### Gmail

Search Gmail for recent email threads related to the meeting topic. Use `gmail_search_messages` with the meeting name or key topic as the query. Look for:

- Pre-read materials or agendas sent by the organizer
- Email threads discussing the meeting topic that contain decisions, context, or action items
- Prep instructions (e.g., "please come prepared with your Q2 OKRs")

This is especially valuable when the user provides minimal context — email threads often contain the richest source of meeting background.

### Weekly Priorities

Check the current week's planning file at `02-AreasOfResponsibility/Weekly Recaps/` (the most recent `YYYY-WNN.md` file). If it exists, extract the priorities section. This provides context about what the user is focused on this week, which helps identify which agenda items matter most and surfaces relevant work that might not be in Todoist or the plan.

### Direct Report Cadence Check

This subsection only runs when `is_direct_report = true` and a recurring note file exists.

**Goal:** Determine which structured check-in sections to include in the meeting note based on meeting history.

**Step 1: Read the note's YAML frontmatter.** Extract the following fields (treat missing fields as null):
- `last_pulse_date` — date the Engagement Pulse section was last included
- `last_skill_date` — date the Skill Development section was last included
- `last_goals_date` — date the Quarterly Goals Review was last included

**Step 2: Count past meetings.** Use Grep or Bash to count `## YYYY-MM-DD` heading lines in the note body:
```bash
grep -c "^## [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" "{note-file-path}"
```
Also collect the list of those dates to determine how many meetings occurred after each `last_*_date`.

**Step 3: Determine which sections to include:**
- **Priorities check**: Always include
- **Tactical**: Always include
- **Engagement Pulse**: Include if `last_pulse_date` is null, OR the number of `## YYYY-MM-DD` sections dated after `last_pulse_date` is ≥ 2
- **Skill Development**: Include if `last_skill_date` is null, OR the number of `## YYYY-MM-DD` sections dated after `last_skill_date` is ≥ 2
- **Quarterly Goals Review**: Include if `last_goals_date` is null, OR `floor((today_month - 1) / 3) != floor((last_goals_month - 1) / 3)` — i.e., today is in a different calendar quarter than `last_goals_date`

**Step 4: Extract prior responses for carry-forward.** If Engagement Pulse or Skill Development is being included, scan the most recent `## YYYY-MM-DD` date section in the note for a `### Direct Report Check-in` subsection. Extract any content under `- Engagement Pulse` and `- Skill Development` headings to use as carry-forward context in Phase 3.

Store the results of this phase as:
- `include_pulse` (bool)
- `include_skill` (bool)
- `include_goals` (bool)
- `prior_pulse_summary` (text or null)
- `prior_skill_summary` (text or null)

### CheckWithContact Tasks

This subsection only runs for **1:1 meetings**. After resolving the attendee's full name via `find_contact` in Phase 0, query Todoist for tasks marked with the `@CheckWithContact` label that contain the attendee's first name in the task content (formatted as `[{first name}] {content}`).

Use `find-tasks` with filter: `@CheckWithContact & search: {first_name}` where `first_name` is the first name extracted from the canonical contact name resolved in Phase 0. These tasks represent talking points or items the user wants to check on with this specific person.

Collect these tasks separately from other Todoist tasks for later classification.

### User-Provided Context

Parse any notes, conversation excerpts, or bullet points the user provided. These often contain the most current information — things that haven't made it into Todoist or the plan yet.

### Project Tag Inference

Using the project index injected into context (from the hook), attempt to identify which project this meeting is associated with. The project index lists each project with its display name, folder name (in backticks after `folder:`), description, area, and due date.

**Matching logic (check in order):**

1. If the user explicitly referenced a PLAN.md path or Todoist project name → use that project's folder name directly. Mark **HIGH** confidence.
2. Otherwise compare the meeting title and calendar event description against each project's display name and description. A match requires ≥ 2 consecutive words (each ≥ 4 characters) from the project name appearing in the meeting title or calendar description, case-insensitive.

**Confidence tiers:**

- **Exactly one project matches** → `inferred_project_tag = snake_case(folder_name)`, `tag_confidence = HIGH`
- **Two or more projects match** → `inferred_project_tag = null`, `tag_confidence = AMBIGUOUS`, store candidate list
- **No project matches** → `inferred_project_tag = null`, `tag_confidence = NONE`

**Snake_case rule:** Lowercase the folder name, replace spaces and hyphens with `_`, strip other non-alphanumeric characters.

## Phase 2: Classify Items

Go through every piece of information gathered and classify each item into one of four categories:

**Decision** — Something that needs to be decided in this meeting. Signals: open questions in the plan, items where multiple options exist and no one has chosen, items the user described as "need to decide" or "TBD." Decisions are the most valuable use of meeting time, so they get prominent placement.

**Status update** — Something actively in progress where the group just needs awareness. Signals: tasks with assignees and due dates, items the user described as "working on" or "in progress." Quick — one bullet, one sub-bullet of context.

**Pending work** — Implementation tasks that don't need individual meeting discussion but the group should know exist. Signals: unchecked tasks in the plan that aren't blocked by a decision, Todoist tasks with no particular urgency. These get rolled up under a parent bullet.

**Talking points** — Items from CheckWithContact tasks (1:1 meetings only). These are topics the user wants to discuss or check on with this person. They're distinct from the four main categories and appear in a dedicated section.

**Open question** — Strategic or process questions where the gap is acknowledged but there may not be a clear decision to make yet. Signals: "we don't know how to," "need to figure out," "no clear approach." Discussion starters at the end.

## Phase 3: Build the Agenda

### Direct Report Check-in Section

When `is_direct_report = true`, build a `### Direct Report Check-in` section using the flags from Phase 1. This section is positioned **between `### My Topics` and `### Their Topics`** in the meeting note.

Always include:

```
### Direct Report Check-in

- Priorities
	- What are your priorities this week?

- Tactical
	- Where would coaching, feedback, or guidance help? Any blockers to clear?
```

If `include_pulse = true`, add:

```
- Engagement Pulse
	- Certainty: Do they have clarity on what's expected and how success is measured?
	- Autonomy: Do they feel ownership over how they get their work done?
	- Meaning: Is the work feeling worthwhile and connected to something bigger?
	- Progress: Do they feel like they're moving forward — in their work and their growth?
	- Social inclusion: Do they feel valued and connected to the team?
```

If `prior_pulse_summary` is not null, add as a final sub-bullet under Engagement Pulse:
```
	- Last time: {prior_pulse_summary}
```

If `include_skill = true`, add:

```
- Skill Development
	- What skill or knowledge area are you actively working on?
	- What action did you take on that in the past week?
	- What action will you take in the coming week?
```

If `prior_skill_summary` is not null, add as a final sub-bullet under Skill Development:
```
	- Last time: {prior_skill_summary}
```

If `include_goals = true`, add:

```
- Quarterly Goals Review
	- Where do you want to develop this quarter?
	- How does your current work ladder up to that growth?
	- What support do you need from me?
```

Use tab characters (not spaces) for all indentation in this section.

---

Structure the agenda under `### My Topics` following these rules:

**Ordering:**

1. Talking points (1:1 meetings only, if any CheckWithContact items exist)
2. Status updates (quick, builds shared context for the decisions)
3. Decisions (the meat of the meeting)
4. Pending work (rolled up, informational)
5. Open questions (discussion starters at the end)

**Formatting:**

- Top-level bullet = short topic label, plain text, no bold or other markdown formatting
- Indented sub-bullet (one tab) = one sentence of context explaining why it matters or what the ask is
- Sub-sub-bullets (two tabs) for items grouped under a parent like "Work that is still pending"

**Talking points (CheckWithContact items):** Group CheckWithContact tasks under a top-level bullet called "Check-ins with {Name}" (where {Name} is the attendee's name). For each task, remove the `[{Name}]` prefix from the task content and list it as a sub-bullet. Example:
```
- Check-ins with Alice Smith
	- Review Q2 project timeline
	- Discuss capacity for new initiative
```

**Grouping pending work:** If there are 3+ pending implementation tasks, roll them up under a single top-level bullet called "Work that is still pending" with each task as a sub-bullet. If there are only 1-2, they can stand alone.

**Carry-forward items:** If the previous meeting note had a `### For Next Time` section with items, include those in the agenda. They represent commitments or topics that were explicitly deferred.

**Keep it tight:** Each sub-bullet should be one sentence. The user will elaborate verbally — the note is a reference, not a script.

### Project Tag Confirmation

Before presenting the agenda, resolve the final tag to apply:

- **HIGH confidence:** Append a one-liner to the agenda presentation: *"I'll tag this note as `{inferred_project_tag}` — correct?"* If the user confirms or doesn't object, proceed. If they correct it, update `inferred_project_tag` to the folder name they specify (or null if they say none).
- **AMBIGUOUS:** Before writing the note, present a short numbered list: *"Which project is this meeting for?"* followed by each candidate tag and *"None — leave blank."* Wait for the user's selection and update `inferred_project_tag`.
- **NONE:** Skip silently — no prompt, no tag.

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

**Apply project tag:** If `inferred_project_tag` is non-null (after Phase 3 confirmation), write `tags: [inferred_project_tag]` in the frontmatter. If null, write `tags: []`. Treat any existing `<optional_project_name>` placeholder in the frontmatter the same as absent — always replace it.

Replace `MEETING_DATE` with the date from the calendar event (or today if no event was found) in a YYYY-MM-DD format.

**Direct report frontmatter update (recurring notes only):** If `is_direct_report = true`, also update the note's YAML frontmatter to record which sections were included today. Do this as a separate Edit after inserting the date section:

- If `include_pulse = true`, set `last_pulse_date` to today's date (YYYY-MM-DD)
- If `include_skill = true`, set `last_skill_date` to today's date
- If `include_goals = true`, set `last_goals_date` to today's date

Handle three cases:
1. **Fields already exist in frontmatter** — use Edit to replace each field line: `old_string: "last_pulse_date: "` → `new_string: "last_pulse_date: 2026-04-16"` (etc.)
2. **Note created from template (new note)** — template already includes the fields; update in the same step as creating the file
3. **Note predates this feature (fields missing)** — add all three fields before the closing `---` of the frontmatter. Use the closing `---` as the anchor: append the missing fields before it

### New meetings (no existing note)

Create the file at `02-AreasOfResponsibility/Notes/{meeting name}.md` using the template from "./templates/adhoc-meeting.md" with the date and agenda items filled in.

Replace `MEETING_DATE` with the date from the calendar event (or today if no event was found) in a YYYY-MM-DD format.

**Apply project tag:** If `inferred_project_tag` is non-null (after Phase 3 confirmation), write `tags: [inferred_project_tag]` in the frontmatter. If null, write `tags: []`. Treat any existing `<PROJECT_TAG>` placeholder the same as absent — always replace it.

**Note on direct report 1:1 notes:** For new recurring 1:1 notes created for direct reports, the template already includes `last_pulse_date`, `last_skill_date`, and `last_goals_date` fields. Set any triggered sections' dates to today when writing the initial file.

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
