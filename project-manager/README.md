# Project Manager

Project planning and tracking plugin for Claude Code. Five skills that take a project from idea to structured plan, keep it connected to Todoist, and surface health signals before things drift.

The project-manager plugin is a domain plugin. It owns the project folder schema and the project index hook. The `chief-of-staff` plugin calls into it during `/start-week` and `/wrap-week` for project status, but all skills can be run independently.

---

## Prerequisites

### Todoist (required)

```bash
claude mcp add --transport http --scope global todoist https://ai.todoist.net/mcp
```

Each project is assumed to have a matching Todoist project with the same name. `/new-project` creates the Todoist project for you; existing projects need to be matched manually.

### Obsidian vault

Projects live in your vault under `01-Projects/` by default. All path defaults can be overridden via `CLAUDE.md` config or per-invocation arguments — see the chief-of-staff README for the full configuration reference.

---

## Skills Reference

| Skill | Description | When to use |
|-------|-------------|-------------|
| `/project-manager:new-project` | Creates an Obsidian project folder and matching Todoist project, then hands off to `project-planner` or `project-tracker` | Starting any new project |
| `/project-manager:project-planner` | Interviews you and writes a structured, phased `PLAN.md` with objectives, tasks, and exit criteria | When you own the project and need a real plan |
| `/project-manager:project-tracker` | Creates a lightweight tracking doc for a project someone else owns — for following progress in 1:1s | When you're monitoring a report's or partner's project |
| `/project-manager:project-monitor` | Compares active `PLAN.md` files against live Todoist tasks — surfaces stalls, task gaps, and approaching deadlines | On demand, or silently by `/wrap-week` |
| `/project-manager:project-index` | Fast index of all active projects from `PLAN.md` frontmatter — names, descriptions, areas, due dates | On demand, or automatically via hook by other skills |

### Arguments

**`/project-manager:new-project`**
- `--projects-path <path>` — Override projects root folder (default: `01-Projects`)

**`/project-manager:project-planner`**
- `--projects-path <path>` — Override projects root folder (default: `01-Projects`)

**`/project-manager:project-tracker`**
- `--projects-path <path>` — Override projects root folder (default: `01-Projects`)

**`/project-manager:project-monitor`**
- `--projects-path <path>` — Override projects root folder (default: `01-Projects`)
- `--summary` — Run in silent summary mode (no interaction, structured output only — used by `/wrap-week`)

**`/project-manager:project-index`**
- `--projects-path <path>` — Override projects root folder (default: `01-Projects`)

---

## Vault Structure

```
01-Projects/
├── my-project/
│   ├── PLAN.md          ← phased plan with frontmatter (name, description, area, due_date, tags)
│   └── Notes/           ← project-specific meeting notes (optional)
└── Watched/
    └── their-project/
        └── PLAN.md      ← lightweight tracker (no phases, just context + tasks)
```

**`PLAN.md` frontmatter** is the contract between this plugin and everything that consumes it:

```yaml
---
name: Project Name
description: Keyword-rich summary — include system names, team names, problem domain. Used for machine matching.
area: Area of Responsibility
due_date: 2026-06-30
tags: [project_tag]
---
```

The `description` field is injected into context by the project-index hook and read by `chief-of-staff` during planning sessions. Write it like a dense search snippet, not a polished summary.

The `tags` field links meeting notes to projects — `/exec-assistant:meeting-prep` and `/exec-assistant:process-transcripts` use it to tag notes with the relevant project.

---

## Tips

**`/project-tracker` vs. `/project-planner`.** Tracker is for watching someone else's work (your reports, cross-functional partners). Planner is for structuring work you own. Don't use planner for observation — it creates false accountability for work you don't control.

**`/project-monitor` runs inside `/wrap-week` automatically.** You don't need to run it on Fridays — wrap-week invokes it silently and uses its output to inform priority-setting. Run it independently mid-week when you want a focused health check.

**Project descriptions are for machines.** The `description` field is read by the hook script and injected into planning and meeting prep context. The richer and more specific it is, the better the automatic project matching in meeting notes and transcripts.

**Todoist project names must match exactly.** `/project-monitor` finds Todoist tasks by searching for a project whose name matches the `PLAN.md` `name` field. Keep them in sync — use `/new-project` to create both at once and avoid drift.
