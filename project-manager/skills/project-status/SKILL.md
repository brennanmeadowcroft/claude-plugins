---
name: project-status
description: "Synthesize current status for a project from PLAN.md, live Todoist tasks, and recent meeting notes tagged to that project. Returns what's in flight, what's next from the plan, and what meetings have surfaced — giving a single, concrete picture of where a project stands. Standalone: interactive report with suggested next steps. Summary mode (--summary): compact structured output consumed by /start-day and other skills. Trigger on 'project status', 'how is [project] going', 'what's next on [project]', 'where does [project] stand', or invokes /project-status. Must be run from the root of the Obsidian vault."
argument-hint: "--project <name> [--summary] [--projects-path <path>] [--notes-path <path>]"
---

# Project Status

You synthesize the current status of a project by combining three sources of truth: the project plan (PLAN.md), live Todoist task state, and recent meeting notes. The goal is a concrete, actionable picture of where the project stands and what should happen next — not a health check, but a status briefing.

## Arguments

- `--project <name>` — project name or folder name to report on (required)
- `--summary` — silent structured output for use by other skills; no user interaction
- `--projects-path <path>` — override projects folder (default: `01-Projects`)
- `--notes-path <path>` — override meeting notes folder (default: `02-AreasOfResponsibility/Notes`)

## Configuration

If a `CLAUDE.md` exists at the vault root with a **Chief of Staff** config block, path values there are used as defaults. Precedence:

1. Per-invocation argument (highest)
2. `CLAUDE.md` Chief of Staff block
3. Hardcoded default

Example `CLAUDE.md` block:

```
## Chief of Staff
- projects-path: Projects
- notes-path: Meetings
```

---

## Phase 0: Setup

**Resolve vault paths** using the precedence above. Get today's date:

```bash
echo "TODAY=$(date +%Y-%m-%d)"
```

---

## Phase 1: Find and Read the Project Plan

Glob `<projects-path>/*/PLAN.md` (and `<projects-path>/*/*/PLAN.md` for nested subfolders like `Watched/`). Read the frontmatter of each to collect `name`, `description`, `due_date`, and `area`.

Match `--project` against project names and folder names (case-insensitive, partial match allowed). If multiple projects match, pick the closest by name-word overlap. If no match is found, print an error listing available projects and stop.

Read the matched project's full PLAN.md. Extract:

- Project name, objective, success criteria
- The **current active phase**: the first phase that has unchecked task items (`- [ ]`) — this is the phase in progress
- The **next phase**: the phase immediately after the current active phase (its intent and key questions, even if not fully planned)
- `## Updates` section: the 3 most recent entries (for context on recent decisions and momentum)
- `due_date` if set in frontmatter

Derive the **project tag**: lowercase the folder name, replace spaces and hyphens with underscores (e.g., `Day Manager` → `day_manager`). This tag is used to find related meeting notes.

---

## Phase 2: Load Todoist State and Meeting Notes (run in parallel)

**Todoist:** Fetch tasks using `find-projects` to locate the matching Todoist project by name, then `find-tasks` filtered to that project. Collect:

- Open tasks (with due dates if set)
- Tasks completed in the last 14 days
- Overdue tasks (open and past due date)
- Tasks with no due date

**Meeting notes:** Scan `<notes-path>/` for `.md` files whose YAML frontmatter `tags` field contains the project tag. Sort by file modification time, most recent first. Take up to 3 matching files.

For each matching note:
- If the filename matches the pattern `{Name} - {Year}.md` or `{Title} - {Year}.md` (recurring note), read only the **last 150 lines** of the file — these contain the most recent meeting entries.
- Otherwise (ad-hoc note), read the full file.

From each note, identify: meeting date (look for `## YYYY-MM-DD` headings), key decisions made, blockers or risks raised, and any action items mentioning the user that haven't been closed.

---

## Phase 3: Synthesize

### Status classification

Assign one status (apply highest-severity that fits):

1. `overdue` — past `due_date` with open tasks remaining
2. `approaching-deadline` — `due_date` within 14 days, open tasks remain
3. `needs-attention` — stalled AND has blocking meeting context, or ≥3 open tasks with no due dates and no recent Todoist activity
4. `stalled` — no Todoist activity (completions or additions) in 14 days
5. `on-track` — everything else

### Next step determination

Determine the single best next action using this priority order:

1. First overdue open Todoist task (most urgent)
2. First open Todoist task due soonest
3. First unchecked task from the current active PLAN.md phase that has no matching open Todoist task (plan has work Todoist doesn't know about)
4. First task or intent from the next PLAN.md phase (current phase may be complete in Todoist but plan has the next phase outlined)
5. `"Review the plan — no tasks defined for the current phase"`

### Blocker identification

A blocker exists when any of the following are true:
- A recent meeting note explicitly calls out a blocker, dependency, or open question that hasn't been resolved
- An open Todoist task has a description mentioning a blocker or waiting-on
- A PLAN.md open question from the current phase has not been addressed in recent Updates entries

Summarize in plain language. If multiple blockers exist, pick the most critical one.

### Meeting context

Use the most recent matching meeting note that has substantive content about this project. Extract: date, one-sentence summary of the most important decision or discussion point, and any action items still open.

---

## Phase 4: Output

### Summary mode (`--summary`)

Return only this structured block — no prose, no additional text before or after:

```
PROJECT: {name}
STATUS: {status}
PHASE: {current active phase name, or "—" if none}
NEXT_STEP: {concrete next action, 1 sentence}
BLOCKERS: {blocker description, or "none"}
LAST_MEETING: {YYYY-MM-DD — 1-sentence key point, or "none"}
SUGGESTION: {1-sentence recommendation for what to do today to move this project forward}
```

Exit immediately after printing. No user interaction.

---

### Standalone mode

Present the full status report:

```
## {Project Name}

**Status:** {emoji + label}  ·  **Deadline:** {due_date or "none"}  ·  **Phase:** {current phase name or "—"}

### What's in Flight

{Open Todoist tasks, grouped: overdue first (flagged 🚨), then by due date, then undated. If none: "No open tasks in Todoist."}

### Completed Recently (last 14 days)

{List of recently completed Todoist tasks. "None in the last 14 days." if empty.}

### What's Next (from the plan)

{Next 1–3 unchecked tasks from the current PLAN.md phase not yet reflected in Todoist, or first tasks/intent from the next phase if the current phase appears done. Explain why these are next.}

### Meeting Context

{For each of the last 1–3 relevant meeting notes, one entry:}
- **{YYYY-MM-DD}** ({meeting name}): {1–2 sentence summary of key decision, outcome, or blocker raised}
  {Open action items from that meeting not yet in Todoist, if any}

{If no meeting notes found: "No meeting notes tagged to this project yet."}

### Suggested Next Step

**{Concrete action}** — {2–3 sentence rationale tying together plan state, Todoist gaps, and meeting context. Make the case for why this specific thing today.}

### Blockers

{List blockers with source (meeting note, plan open question, or task dependency). "None identified." if clear.}
```

Status emoji:
- `on-track` → ✅
- `stalled` → 🔄
- `needs-attention` → ⚠️
- `approaching-deadline` → 🔔
- `overdue` → 🚨

After presenting the report, ask:

> What would you like to do?
> 1. Add the next plan tasks to Todoist
> 2. Log a status note to the plan (Updates section)
> 3. Nothing — just reviewing

Handle the chosen action:

- **Option 1:** For each task from "What's Next" the user confirms, call `create-task` with the task content, the Todoist project, and the PLAN.md phase as the description context. Confirm how many were created.
- **Option 2:** Append an `## Updates` entry to PLAN.md using the Edit tool:
  ```markdown
  ### {TODAY}
  
  {User-provided status note, or a summary of what you synthesized if the user says "write it for me"}
  ```
- **Option 3:** Exit without action.
