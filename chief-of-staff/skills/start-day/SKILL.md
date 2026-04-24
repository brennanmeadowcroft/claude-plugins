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
- `--projects-path <path>` — override projects folder (default: `01-Projects`)

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
- projects-path: Projects
```

## Vault Paths (relative to vault root)

- Daily notes: resolved `daily-notes-path` (default: `02-AreasOfResponsibility/Daily Notes/`)
- Meeting notes: resolved `notes-path` (default: `02-AreasOfResponsibility/Notes/`)
- Weekly recaps: resolved `weekly-recaps-path` (default: `02-AreasOfResponsibility/Weekly Recaps/`)
- Projects: resolved `projects-path` (default: `01-Projects/`)

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

**Gmail — priority emails:** Call the Gmail MCP server to search for emails with high-priority labels. Use the query:
```
label:Priority/p1 OR label:Priority/p2
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

Before presenting the briefing, synthesize a **Focus Recommendation** based on today's calendar and weekly priorities. This should be ready before the user reads anything else.

**Project status enrichment:** Before forming the recommendation, enrich each weekly priority with live project context:

1. Glob `<projects-path>/*/PLAN.md` (and `<projects-path>/*/*/PLAN.md` for nested folders like `Watched/`) to collect project names and folder names. Read frontmatter only — not the full file.
2. For each weekly priority, match it to the most relevant project by name-word and description overlap (case-insensitive). It is fine if a priority has no matching project.
3. For each matched project, invoke `project-status` in summary mode via the Skill tool:
   ```
   Skill("project-status", "--summary --project \"{matched-project-name}\"")
   ```
   Run all project-status calls in parallel.
4. Parse the returned `STATUS`, `NEXT_STEP`, `BLOCKERS`, `LAST_MEETING`, and `SUGGESTION` fields. Store them alongside the weekly priority.

Use these enriched results as the primary input for Today's Focus and Morning Intentions — concrete project state beats a raw Todoist task list.

Cross-reference:
- Weekly priorities (from WEEK_NUM.md) — what are the 2–3 things that matter this week?
- Project status results — what is the actual next step for each priority's project? Is anything stalled, blocked, or approaching a deadline?
- Today's calendar gaps — where are the 60+ minute uninterrupted windows?
- Today's priority Todoist tasks — which best serve the weekly priorities (use as a supplement, not the primary input)?
- Meeting relevance — do any of today's meetings connect to a weekly priority? Weave in `LAST_MEETING` context from project-status where available.

Form a concrete recommendation: for each meaningful focus window, say what the user should work on and why — rooted in project state, not just task lists. This is not a list of options — it's a recommendation. The user can redirect it.

**Delegate quick tasks before presenting.** After synthesizing the briefing but before presenting it, scan for 1–3 quick delegations — things like updating a meeting agenda, rescheduling a stale task, or labeling an email. For each one found, fire a background agent with the relevant skill and the specific detail. Note each delegation under a **Delegated** line in Today's Focus so the user sees what's already in motion. Do not discuss these with the user — just do them and report. Example skills to delegate to:
- `exec-assistant:meeting-prep` — if a meeting today has no agenda prepped
- Google Calendar MCP — reschedule a conflicting event
- Todoist reschedule — move an obviously stale overdue task

Present the briefing in this structure:

---

### Good [morning/afternoon] — [DAY_NAME], [Full Date]

**Today's Focus** ← lead with this, not at-a-glance
Based on your weekly priorities and project status:

- **[Focus window 1, e.g., "9:00–11:00"]** → [Priority name]: [NEXT_STEP from project-status, or specific Todoist task if no project match] — [1-sentence reason grounded in project state, e.g., "project is on-track and this is the next planned step" or "project is stalled — this unblocks the next phase"]
- **[Focus window 2 if any]** → [same pattern]

[If project-status returned a BLOCKER for a priority:] "⚠️ [Priority name] is blocked: [BLOCKER]. Your [meeting today / this week] with [Person] may be the right moment to resolve this."

[If a meeting today is relevant to a weekly priority:] "Your [Time] with [Person] connects to priority #[N] — [LAST_MEETING context from project-status if available, otherwise 1 sentence from prior meeting notes]"

[If no clear focus windows exist:] "Today is back-to-back — the best window is [small gap]. Consider whether any meetings are optional."

[If any priority's project has STATUS=stalled or needs-attention:] "⚠️ [Project name] hasn't had activity in [N] days — consider addressing this in your next available window."

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

**Focus Windows** (only if not already covered in "Today's Focus" at top)
If `[IT]` blocks exist on the calendar, list them here. If additional unscheduled gaps exist beyond what was recommended above, note them briefly. Don't re-surface the same recommendation — this section supplements, not repeats, "Today's Focus."

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

For each weekly priority, state what movement looks like today using the project-status enrichment from Phase 2. Use `NEXT_STEP` as the primary supporting action. If no project match was found, fall back to the first relevant Todoist task.

- **[Weekly Priority]** — [what "done" or "moved forward" looks like today, grounded in project state]
  - [NEXT_STEP from project-status, or first relevant Todoist task]
  - [second supporting task if one exists and is clearly relevant]

- **[Weekly Priority]** — ⚠️ [stalled / no tasks / blocked — use STATUS + BLOCKERS from project-status]
  - [NEXT_STEP from project-status if available, even if Todoist has nothing]
  - [If NEXT_STEP is unavailable: → Run /project-status to surface next steps, or review [[Projects/[Project Name]/PLAN.md]]]

## Schedule

[Calendar events, one per line with times]

## Meeting Notes

[Wiki-links to today's relevant meeting notes, e.g., [[1:1 with Alex]], [[Team Standup]]]

## Notes

## End of Day
<!-- Filled in by /finish-day -->
```

If a daily note already exists, use the Edit tool to add or update only the "Morning Intentions" section.

## Decision Tracking

As you work through this session, watch for decision signals from the user — statements like "I don't need that", "we already have a task for this", "we decided to go with X", "that's not relevant to me anymore", "skip that". When you encounter one:

- **Scope:** Is this tied to a specific project being discussed? → write to `01-Projects/<project>/decisions.yaml`. Otherwise → write to `decisions.yaml` at vault root.
  - Email and task dispositions are always global.
  - Approach and architecture decisions are project-scoped if a project is clearly in context; otherwise global.
- **Write immediately** — don't wait until the end of the session. Use file write or a Bash heredoc append.
- **Don't call it out** unless you're uncertain about scope or TTL — just capture it silently.
- **Entry format:** generate ID as `dec_YYYYMMDD_<4 hex chars>`, set `created` to today, set `expires` using the TTL tier that fits:
  - `email` / `task` → +7 days
  - `approach` / `process` → +21 days
  - `strategic` → +90 days

```yaml
- id: dec_20260422_a1b2
  text: "Todoist task 'Review Q2 roadmap' already captured as #123456789 — skip"
  category: task
  created: 2026-04-22
  expires: 2026-04-29
```

If the file doesn't exist yet, create it. Preserve all existing entries.

## Quality Notes

- Always use the date from Bash, never infer it
- Lead with "Today's Focus" — it's the most valuable part of the briefing. Don't bury the recommendation at the end.
- The recommendation should be specific and opinionated: "work on X" not "you could work on X or Y." The user can override it.
- If no weekly priorities file exists, the recommendation falls back to urgency (overdue + p1 tasks). Note that `/start-week` would make this more useful.
- Priorities should reflect both urgency (due dates, overdue status) and importance (Todoist priority levels)
- Keep the briefing scannable — headers and bullets, not paragraphs
- Meeting note wiki-links use Obsidian format: `[[Note Name]]`
- If no meeting notes are found for today, omit that section — it means `/finish-day` wasn't run last night
- @Process_Task items that are due today or overdue should also appear in "Top Priorities" — the Process Tasks section surfaces them as a group, but they still count toward urgency ranking
- The skill ends after Phase 3. Do not continue into task execution, rescheduling, email drafting, or acting on individual tasks raised in the briefing. If the user engages on a specific task, respond with one sentence of context and suggest they handle it after the briefing. The goal is to leave the user oriented, not to start working the list together.
- During Phase 2, identify 1–3 quick delegations (agenda prep, reschedules, labels) and fire them as background agents before presenting the briefing. Note each under a "Delegated" line in Today's Focus so the user sees what's already in motion. Do not discuss these with the user — just do them and report.
- If a weekly priority has no tasks due this week or this month, flag it explicitly in Morning Intentions — don't silently skip it. Surface the project plan path or suggest /project-monitor so the user knows where to look for next steps.
