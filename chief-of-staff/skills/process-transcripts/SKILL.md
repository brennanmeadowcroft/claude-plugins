---
name: process-transcripts
description: Process meeting transcripts into structured Obsidian meeting notes and Todoist action items. Finds transcripts in ~/Nextcloud/Meeting Uploads/, generates AI summaries, writes them into the correct note file, and creates tasks from action items. Trigger when the user says "process transcripts", "process my meeting transcripts", "summarize my meetings", or invokes /process-transcripts. Also invoked automatically by /finish-day. Must be run from the root of the Obsidian vault.
---

# Process Transcripts

You are helping the user turn raw meeting transcripts into structured meeting notes. For each meeting, you will read the transcript, generate a comprehensive summary, write it into the appropriate Obsidian note, and create Todoist tasks for any action items.

## Arguments

- `--notes-path <path>` — override meeting notes folder (default: `02-AreasOfResponsibility/Notes`)
- `--date <YYYY-MM-DD>` — the meeting date to process (default: today)
- `--meeting <name>` — process only this single meeting by calendar event title
- `--note-file <path>` — explicit path to the Obsidian meeting note (bypasses auto-detection)
- `--transcript-file <path>` — explicit path to the transcript file (bypasses auto-detection)

## Configuration

If a `CLAUDE.md` exists at the vault root with a **Chief of Staff** config block, the `notes-path` value there is used as the default — no argument needed. The precedence is:

1. `--notes-path` argument (highest)
2. `notes-path` in `CLAUDE.md` Chief of Staff block
3. Hardcoded default: `02-AreasOfResponsibility/Notes`

Example `CLAUDE.md` block:

```
## Chief of Staff
- notes-path: Meetings
```

## Vault Paths (relative to vault root)

- Meeting notes: resolved `notes-path` (default: `02-AreasOfResponsibility/Notes/`)
- Transcript base directory: `~/Nextcloud/Meeting Uploads/`

If both `--note-file` and `--transcript-file` are provided, skip Phases 1 and 2 and jump directly to Phase 3.

---

## Phase 0: Setup

**First, resolve the notes path.** Check `CLAUDE.md` at vault root for a "Chief of Staff" section and read the `notes-path` value if present. If `--notes-path` was passed, it overrides the CLAUDE.md value. If neither is set, use `02-AreasOfResponsibility/Notes`. Use the resolved path everywhere below.

Get today's date via Bash:

```bash
echo "TODAY=$(date +%Y-%m-%d)"
```

If `--date` was passed, use that value. Otherwise use TODAY.

---

## Phase 1: Identify Meetings

Skip this phase if both `--note-file` and `--transcript-file` were provided.

**If `--meeting <name>` was passed:** Process only that one meeting — treat it as a single-item list.

**Otherwise:** Call `list-events` on the Google Calendar MCP server for the target date. Collect all events, excluding:
- All-day events
- Events with titles starting with `[IT]` (focus blocks)
- Declined events

Use each event title as the meeting name.

### Derive transcript filename

For each meeting name, derive the expected transcript filename:
1. Lowercase the entire name
2. Replace every non-alphanumeric character (`[^a-z0-9]`) with `_`
3. Append `_transcript.txt`

Examples:
- `"Brennan / Rob"` → `brennan___rob_transcript.txt`
- `"Team Sync"` → `team_sync_transcript.txt`
- `"1:1 with Alice"` → `1_1_with_alice_transcript.txt`

### Check for transcript files

For each meeting, attempt to read the file at:
```
~/Nextcloud/Meeting Uploads/{date}/{derived_filename}
```

Use the Read tool. If the file is not found, mark the meeting as **skipped (no transcript)**.

### Report findings

Before proceeding, show the user a brief status:

```
Transcripts found: Meeting A, Meeting B
Skipped (no transcript): Meeting C, Meeting D
```

If no transcripts were found, stop and tell the user.

---

## Phase 2: Locate Meeting Note

Skip this phase if both `--note-file` and `--transcript-file` were provided.

For each meeting with a transcript, find its Obsidian note. Use the same logic as `/meeting-prep`:

### Step 1: 1:1 detection

Check if the calendar event has exactly 2 attendees (the user + one other). If it is a 1:1, resolve the other attendee's full name:
- Call `lookup_contact` with their email address
- If found, use the canonical `name` field
- If not found, use the display name from the calendar event

### Step 2: Search for recurring note

Try Glob for a year-based note:
- **1:1 meetings:** `02-AreasOfResponsibility/Notes/{First Last} - {Year}.md`
- **Group meetings:** `02-AreasOfResponsibility/Notes/{Meeting Name} - {Year}.md`

If found → mark as **recurring**.

### Step 3: Search for ad-hoc note

If no recurring note was found, try:
- `02-AreasOfResponsibility/Notes/{Meeting Name}.md`

If found → mark as **ad-hoc**.

### Step 4: No note found

If neither search yields a result, skip this meeting and report:
> "No meeting note found for '{Meeting Name}' — run /meeting-prep first to create the note."

---

## Phase 3: Generate Summary

For each meeting (or the explicit `--note-file` / `--transcript-file` pair), generate the meeting summary.

**Step 1: Read the transcript file** using the Read tool.

**Step 2: Read the meeting note.**

- **Recurring meetings:** Extract only the target date's section using Bash — do NOT read the full note file, as it accumulates past meetings and would send irrelevant history to the model:

  ```bash
  bash "${CLAUDE_PLUGIN_ROOT}/skills/process-transcripts/scripts/extract-note-section.sh" "{absolute-path-to-note-file}" "{YYYY-MM-DD}"
  ```

  Save the output as `extracted_notes`. This will be used both as the meeting notes context for the summary prompt and as the `old_string` in Phase 4. If the script exits with an error (section not found), fall back to reading the full note file with the Read tool and warn the user.

- **Ad-hoc meetings:** Read the full note file with the Read tool and save the contents as `extracted_notes`. Ad-hoc notes contain only one meeting's worth of content so there is no need to extract a section.

**Step 2b: Check existing tags.**

From `extracted_notes`, read the YAML frontmatter `tags` field:
- If `tags` is non-empty and not a placeholder (i.e., not `[]`, not `[<PROJECT_TAG>]`, not absent) → set `existing_tag` to that value. No inference needed.
- Otherwise → set `existing_tag = null`. Proceed to Step 2c.

**Step 2c: Tag inference (only when `existing_tag` is null).**

Using the project index injected into context, score each project against the transcript text. The project index lists each project with its folder name in backticks after `folder:`. For each project, count occurrences of its name words (≥ 4 characters each, split on spaces and hyphens) in the transcript text (case-insensitive).

- If one project has ≥ 3 name-word hits AND scores at least 2× the next-highest scorer → `inferred_tag = snake_case(folder_name)` for that project.
- Otherwise → `inferred_tag = null`.

Set `resolved_tag = existing_tag ?? inferred_tag` (use `existing_tag` if non-null, else `inferred_tag`).

**Snake_case rule:** Lowercase the folder name, replace spaces and hyphens with `_`, strip other non-alphanumeric characters.

Then generate a structured summary using the following prompt:

---

> You are an expert meeting notes assistant. Your job is to generate comprehensive meeting notes by consolidating transcript content and user notes.
>
> The meeting date to process is: **{YYYY-MM-DD}**
>
> The meeting notes (agenda and pre-meeting context) are:
> ```
> {contents of meeting note file}
> ```
>
> The meeting transcript is:
> ```
> {contents of transcript file}
> ```
>
> ---
>
> Generate a **JSON object** with exactly two keys:
>
> **1. `"summary"`** — a markdown string using the output format below
>
> **2. `"action_items"`** — an array of objects, each with:
> - `"task"`: string — the action item, self-contained with enough context to be understood standalone
> - `"due_date"`: string or null — ISO date (YYYY-MM-DD) inferred from transcript, or null
> - `"detail"`: string — reasoning or additional context about the action item
> - `"is_process_task"`: boolean — true if someone is explicitly waiting on Brennan for a decision, approval, or response (i.e., Brennan is the blocker); false otherwise
>
> ---
>
> ### Instructions for generating the summary
>
> **Topic Identification:**
> - Identify topics discussed in the transcript
> - Use top-level bullet points from the provided meeting notes as a guide (but not the only source)
> - Include topics discussed in the transcript that weren't in the notes
> - For topics from notes, incorporate all sub-bullet points and expand using transcript details
> - Details should be 2-3 sentence summaries highlighting specific information. Include as many detail bullets as needed to effectively summarize the topic.
> - Highlight action items where Brennan is the blocker, a decision needs to be made, or someone has concerns about a topic
> - If present, ignore any detail under the heading `### Preamble` — those are kickoff notes and not part of the conversation
> - Ignore the note headings `### My Topics` and `### Their Topics` — treat all notes equally
> - If a topic was in the meeting notes but not discussed, include it as a topic but indicate it was not discussed
>
> **Question Answering:**
> - Look for questions in the notes marked with `* [?] question text?`
> - Use the transcript to answer these questions thoroughly, including specific quotes or details when possible
> - Answer concisely but with a minimum of 1-2 sentences (more if the answer requires it)
> - If a question is a sub-bullet, use its parent topic for context
> - If you cannot answer a question from the transcript, include the question but state "Unable to answer from transcript"
> - DO NOT make up answers
>
> **Task Recording:**
> - Include tasks from notes marked with `* [] task text`
> - If a task is a sub-bullet, rewrite it with enough context to be understandable standalone
>
> **Action Items (for the `action_items` array):**
> Identify items where **Brennan has explicitly committed to a deliverable or decision**:
> - Must be something Brennan said he would do, look into, or decide on
> - Include specific context in the `detail` field, referencing what was said
> - Extract or infer due dates when mentioned
> - Set `"is_process_task": true` when another person is explicitly waiting on Brennan for a decision, approval, or response — i.e., Brennan is the blocker. This includes commitments to respond, approve, or decide on something for someone else. Set to `false` for work Brennan is doing independently.
>
> **Exclude from action items:**
> - Guidance or advice Brennan gave to the other person (that's coaching, not a task)
> - Items the other person is going to do or look into
> - Troubleshooting steps discussed live during the meeting that were resolved or moved past
> - Strategic ideas discussed but not tied to a specific Brennan commitment
> - Work Brennan is already doing as part of his ongoing role
>
> **Direct Report Check-in (1:1s with direct reports):**
> If the meeting notes include a `### Direct Report Check-in` section, you MUST include a `### Direct Report Check-in` section in the summary output, positioned after `### Summary` and before `### Follow-Ups`. For each item that appeared in the notes (Priorities, Tactical, Engagement Pulse, Skill Development, Quarterly Goals Review), capture what was said or discussed in the transcript. Use the same bullet names. If a topic was not discussed, write "not discussed." This section must be preserved in full so future meeting prep can carry forward prior responses.
>
> **Discussion Follow-Ups:**
> Capture ideas or themes that got traction but did not resolve into a concrete commitment from anyone:
> - Keep each item to one or two sentences describing the idea and why it matters
> - Do not assign an owner or due date
> - Only include items where there was genuine back-and-forth or expressed interest, not passing mentions
>
> ---
>
> ### Output format for the `"summary"` field
>
> ```
> ## {MEETING_DATE}
>
> ### Summary
> #### Topic 1
> - Key point
>     - Details about the key point
>
> #### Topic 2
> - Key point
>     - Details about the key point
>     - **<question from notes>?**
>         - <answer based on transcript>
>
> #### Topic 3
> - This topic was on the agenda but not discussed in the meeting
>
> ### Direct Report Check-in
> *(only present if meeting notes included this section)*
> - Priorities
>     - {what they said their priorities are}
> - Tactical
>     - {coaching needs or blockers discussed}
> - Engagement Pulse
>     - Certainty: {observations}
>     - Autonomy: {observations}
>     - Meaning: {observations}
>     - Progress: {observations}
>     - Social inclusion: {observations}
> - Skill Development
>     - Skill area: {what they named}
>     - Last week: {what they did}
>     - Next week: {what they plan}
> - Quarterly Goals Review
>     - {what was discussed}
>
> ### Follow-Ups
> - <follow up details>
>
> ### Action Items
> * [ ] <action item>
>     * Reasoning or detail about the action item
> ```
>
> Use tab characters (not spaces) for indentation.
>
> Return ONLY the JSON object. Do not include any text outside the JSON.

---

## Phase 4: Write Summary to Meeting Note

### Recurring meetings

The `## {MEETING_DATE}` section already exists in the note (created by `/meeting-prep`). Use the Edit tool to replace it in-place with the `summary` string from the JSON output.

- Use `extracted_notes` from Phase 3 as the `old_string` — it is the exact content of the date section and does not require re-reading the file.
- All other date sections remain intact.

### Ad-hoc meetings

Keep the YAML frontmatter intact (everything up to and including the closing `---`). Replace the entire body after the frontmatter with the `summary` string from the JSON output.

Use the Edit tool.

### Frontmatter tag update (both meeting types)

After writing the summary, if `resolved_tag` is non-null AND `existing_tag` was null (i.e., inference fired or a tag was derived):

Use the Edit tool to update the `tags` field in the note's YAML frontmatter as a separate edit (the frontmatter is outside the date section replaced above):

- If `tags: []` exists → replace with `tags: [resolved_tag]`
- If `tags: [<PROJECT_TAG>]` exists → replace with `tags: [resolved_tag]`
- If the `tags` field is absent → insert `tags: [resolved_tag]` on the line before the closing `---`

If `resolved_tag` is null, or `existing_tag` was already set, skip this step entirely. No user prompt at any point.

---

## Phase 5: Review and Approve Action Items

Before creating any Todoist tasks, present the full list of action items to the user for review.

Format them as a numbered list so the user can refer to them by number:

```
### Action Items — Review Before Adding to Todoist

1. **Task text** (due: YYYY-MM-DD or "no due date") [Process Task]
   > Detail / reasoning

2. **Task text** (due: ...)
   > Detail / reasoning
```

Include the `[Process Task]` marker only for items where `is_process_task` is true — this shows the user which tasks will be tagged with `@Process_Task` before they approve.

Then ask:

> Which of these should I add to Todoist? You can say "all", "none", give specific numbers (e.g. "1, 3"), or say "skip N" to exclude specific ones.

Wait for the user's response. Parse it to determine which items to create:
- "all" → create every item
- "none" → skip all, proceed to Phase 6
- "1, 3" or "1 and 3" → create only those numbered items
- "skip 2" or "all except 2" → create all except the excluded ones

For each approved item, call `create-task` with:

- `content`: the `task` string
- `due_date`: the `due_date` value (or omit if null)
- `project`: `#Inbox`
- `description`: the `detail` string, followed by a blank line and then: `Source: [[{note filename without .md extension}]]`
- `labels`: `["@Process_Task"]` if `is_process_task` is true (omit otherwise)

After creating tasks, confirm to the user how many were created.

---

## Phase 6: Final Report

Print a summary table:

```
### Transcript Processing Complete

| Meeting | Note | Type | Tasks Created |
|---|---|---|---|
| Brennan / Rob | Rob Smith - 2026.md | Recurring | 3 tasks added (of 4) |
| Team Sync | — skipped: no transcript | — | — |
| Q2 Planning | Q2 Planning.md | Ad-hoc | 1 task added (of 1) |
```

If any meetings were skipped due to missing notes, list them with the reason.
