---
name: project-monitor
description: Compares active project PLAN.md files against live Todoist task state. Identifies stalled projects, task gaps between the plan and Todoist, undocumented work, and approaching deadlines. Can update PLAN.md files and create missing Todoist tasks. Can be run standalone or invoked silently by /wrap-week in summary mode. Trigger when the user says "check my projects", "project health", "project status", "monitor projects", or invokes /project-monitor. Must be run from the root of the Obsidian vault.
---

# Project Monitor

You are helping the user keep their active projects on track. This skill compares what's in each project's PLAN.md against what's actually happening in Todoist — surfacing gaps, stalled projects, undocumented work, and upcoming deadlines before they become problems.

This skill can run in two modes:

- **Standalone** (default): Full interactive session — presents analysis per project, asks the user for decisions, and takes actions (update plans, create tasks, mark complete).
- **Summary mode** (`--summary`): Silent data-gathering only. Returns structured output for another skill (e.g., `/wrap-week`) to consume. No interactive prompts, no actions taken.

## Arguments

- `--projects-path <path>` — override projects folder (default: `01-Projects`)
- `--summary` — run in summary mode (no interaction, structured output only)

## Vault Paths (relative to vault root)

- Projects: `01-Projects/` (each project is a subfolder with a `PLAN.md` file)

---

## Phase 1: Load Projects

Read all `01-Projects/*/PLAN.md` files. From each, extract frontmatter:
- `name` — project name
- `description` — keyword-rich summary
- `due_date` — deadline (optional)
- `area` — owning AOR

Also read the `## Tasks` section of each PLAN.md to get the list of planned tasks.

If no projects are found, note that and skip to closing.

---

## Phase 2: Load Todoist State (run in parallel)

For each project, fetch tasks from the matching Todoist project (match by `name` from frontmatter — use the project name as the Todoist project filter):

- All open tasks
- Tasks completed in the last 7 days
- Task due dates

Categorize per project:
- **Open tasks** — not yet complete
- **Recently completed** — done in the last 7 days
- **Overdue tasks** — past due date
- **No-date tasks** — open but no due date

---

## Phase 3: Gap Analysis

For each project, compare the PLAN.md task list against Todoist:

**Missing tasks:** Tasks listed in PLAN.md's `## Tasks` section that don't have a matching open or completed Todoist task. These may have been completed outside Todoist, skipped, or forgotten.

**Undocumented work:** Open Todoist tasks that have no corresponding item in PLAN.md. The plan may be stale.

**Stalled:** No tasks completed in the last 7 days AND no recently-added open tasks.

**Approaching deadline:** `due_date` is within 14 days and open tasks remain.

**Overdue:** `due_date` is in the past and open tasks remain.

**On track:** Has recent activity, no deadline concern, plan and Todoist are reasonably aligned.

---

## Phase 4: Classify and Report

Assign each project one status: `on-track`, `stalled`, `needs-attention`, `approaching-deadline`, or `overdue`

Priority for classification (apply the highest-severity that fits):
1. `overdue` — past deadline with open tasks
2. `approaching-deadline` — deadline within 14 days with open tasks
3. `needs-attention` — significant task gaps (≥3 missing tasks or ≥3 undocumented tasks)
4. `stalled` — no activity in 7+ days
5. `on-track` — everything else

### Summary mode (`--summary`)

Return a structured list without any user interaction:

```
[Project Name] | status: [status] | due: [due_date or "none"] | note: [1-line flag reason or "—"]
```

Exit after returning the list. No further interaction.

---

### Standalone mode

For each project, present:

```
### [Project Name]
Status: [status emoji + label]  |  Deadline: [due_date or "none"]
Area: [area]

[Gap analysis — only show what's relevant:]
- Missing tasks (in plan, not in Todoist): [list or "none"]
- Undocumented work (in Todoist, not in plan): [list or "none"]
- Overdue Todoist tasks: [list or "none"]
- Last activity: [X days ago / "this week"]
```

Status emoji key:
- `on-track` → ✅
- `stalled` → 🔄
- `needs-attention` → ⚠️
- `approaching-deadline` → 🔔
- `overdue` → 🚨

After presenting all projects, ask the user for their decision on each flagged project (anything not `on-track`). Collect all decisions before executing.

For each flagged project, options:

- **Looks good / skip** — no action
- **Update the plan** → update the `## Tasks` section of PLAN.md to reflect current Todoist state; add an `## Updates` entry with today's date and a brief status note
- **Create missing tasks** → create the missing Todoist tasks in the matching project
- **Add a note** → append an entry to `## Updates` in PLAN.md with a blocker note or status update
- **Mark complete** → ask for confirmation, then archive or mark the project as done (move PLAN.md frontmatter `tags` from `[project]` to `[project, complete]` and add `completed: YYYY-MM-DD`)

---

## Phase 5: Execute Actions (standalone only)

After collecting all decisions:

1. Batch all `add-task` calls for any missing tasks being created
2. Use the Edit tool to update PLAN.md files — update `## Tasks` lists and append `## Updates` entries

When appending to `## Updates`, use this format:

```markdown
### YYYY-MM-DD

[Status note — e.g., "On track. 3 tasks completed this week, 2 remaining before phase 2."]
[Blocker note if applicable — e.g., "Blocked on design review from [person]."]
```

---

## Closing (standalone only)

Summarize actions taken:

```
Project monitor complete.
- [N] projects reviewed
- [X] on track
- [Y] updated
- [Z] tasks created
```

If any projects are `approaching-deadline` or `overdue` and weren't addressed, call them out explicitly:

```
⚠️ Still needs attention:
- [Project Name] — [status] — [due_date]
```
