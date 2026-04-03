---
name: aor-review
description: Reviews the health of each Area of Responsibility by checking open Todoist task counts, task age, and clustering patterns. Surfaces flags, suggests spinning up projects where warranted, and lets the user decide how to handle each area. Can be run standalone or invoked silently by /wrap-week in summary mode. Trigger when the user says "review my areas", "check my areas of responsibility", "AOR review", or invokes /aor-review. Must be run from the root of the Obsidian vault.
---

# AOR Review

You are helping the user check in on their Areas of Responsibility (AORs) — the ongoing domains they own, distinct from time-bound projects. The goal is to surface areas that have accumulated work, identify where a dedicated project might make sense, and make sure nothing important is being neglected.

This skill can run in two modes:

- **Standalone** (default): Full interactive session — presents health signals, asks the user for decisions per area, and takes actions (schedule reviews, spin up projects).
- **Summary mode** (`--summary`): Silent data-gathering only. Returns structured output for another skill (e.g., `/wrap-week`) to consume. No interactive prompts, no actions taken.

## Arguments

- `--areas-path <path>` — override areas of responsibility root folder (default: `02-AreasOfResponsibility`)
- `--summary` — run in summary mode (no interaction, structured output only)

## Vault Paths (relative to vault root)

- Areas of responsibility: `02-AreasOfResponsibility/` (subfolders, excluding `Daily Notes`, `Weekly Recaps`, `Notes`)

---

## Phase 1: Discover Areas

List the subfolders of the areas path (default: `02-AreasOfResponsibility/`). Exclude system folders: `Daily Notes`, `Weekly Recaps`, `Notes`. Each remaining subfolder is one AOR. Its folder name must match the corresponding Todoist project name exactly.

If no subfolders are found (or the path doesn't exist):
- **Standalone:** Tell the user no AOR folders were found and skip to closing.
- **Summary mode:** Return `[]` and exit.

---

## Phase 2: Gather Context (run in parallel)

For each AOR folder:

- Read any `.md` files in that folder to understand the area's scope and objective
- Call `find-tasks` filtered to the matching Todoist project name to fetch all open tasks, including due dates and creation dates

---

## Phase 3: Synthesize Health Per Area

For each area, assess:

**Metrics:**
- Open task count
- Age of the oldest open task (days since creation)
- Whether any tasks are overdue or due this week

**Themes:**
- Brief synthesis of what kinds of work are queued (2–3 words per theme is enough)

**Project readiness signal** — flag if ANY of the following:
- ≥5 open tasks
- Any task is >30 days old
- Tasks appear to cluster around a specific deliverable or initiative

When flagging, state the reason concisely: e.g., "5 tasks around improving CI/CD pipeline — this looks like a project."

---

## Phase 4: Present and Act

### Summary mode (`--summary`)

Return a structured list without any user interaction:

```
[Area Name] | open: X | oldest: Y days | health: ok/flagged | reason: [flag reason or "—"]
```

Exit after returning the list. No further interaction.

---

### Standalone mode

For each area, present:

```
### [Area Name]
Open tasks: X  |  Oldest: Y days old  [⚠️ if >30 days]
Themes: [2–3 sentence synthesis of what's queued]
[💡 Suggested: Consider spinning up a project — [reason]]  ← only if flagged
```

After presenting all areas, collect decisions. Ask the user to respond for each area:

- **Looks good** — no action needed
- **Schedule a review** → create a Todoist task in that project due next Monday: "Review [Area Name]"
- **Spin up a project** → ask for project name → create project stub (see template below)

Collect all decisions before executing. Batch all `add-task` calls together, then write any PLAN.md files.

---

## Project Stub Template

When creating `01-Projects/<Name>/PLAN.md`:

```markdown
---
name: <Project Name>
description: <keyword-rich summary used for machine matching — include system names, team names, business domain, the specific problem and approach. Not a generic summary.>
due_date: <YYYY-MM-DD — omit entirely if no hard deadline>
area: <area-name>
started: <today>
tags: [project]
---

# <Project Name>

## Overview

<2–4 sentence narrative: why this project exists, who's involved, what's driving it, and any important background. Dense enough to get back up to speed before a meeting.>

## Tasks

- [ ] <!-- Relevant open tasks from the [Area Name] Todoist project -->

## Updates

<!-- Filled in over time as the project progresses -->
```

After creating the stub, tell the user: "Run `/project-planner` on this project to build out the full plan with phases, objectives, and exit criteria."

---

## Closing (standalone only)

Summarize actions taken:

```
AOR review complete.
- [N] areas reviewed
- [X] look good
- [Y] reviews scheduled
- [Z] project(s) created: [names]
```

If any projects were created, remind the user to run `/project-planner` to flesh them out.
