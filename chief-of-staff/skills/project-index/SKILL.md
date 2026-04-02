---
name: project-index
description: Returns a lightweight index of all active projects from 01-Projects/ — names, descriptions, areas, and due dates extracted from PLAN.md frontmatter. Designed to be called by other skills (start-week, finish-day, etc.) as a fast project context lookup. The plugin hook runs the extraction automatically when this skill is invoked. Trigger on "list my projects", "what projects do I have", or when invoked by another skill.
---

# Project Index

You are providing a fast, lightweight index of the user's active projects. The project data has been extracted from `01-Projects/*/PLAN.md` frontmatter by the plugin hook and injected into this context above.

## What to do with the hook output

The hook has already run `hooks/extract_frontmatter.py` and provided the project list as additional context. Present it clearly, then stop — do not read any PLAN.md files unless the user asks for detail on a specific project.

If the hook output indicates no projects or no `01-Projects/` folder, say so and suggest running `/project-planner` to create the first project.

## When called by another skill

If this skill was invoked by another skill (e.g., `/start-week`), return the project index as structured context for that skill to use. Do not present it as a standalone briefing — just make the data available.

## Fallback (hook not running)

If no project index appears in context above, the hook may not be configured or the script may have failed. Read each `PLAN.md` file directly using the Read tool and extract `name`, `description`, `due_date`, and `area` from the frontmatter manually.
