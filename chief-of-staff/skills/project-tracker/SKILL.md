---
name: project-tracker
description: Use this skill whenever a user wants to capture or set up a lightweight tracker for a project owned by someone on their team — not a full project plan, but a quick reference doc for checking progress in 1:1s. Trigger on phrases like "track this project", "set up a tracker", "I want to keep tabs on", "capture this project", "my report is working on", "log a project for my 1:1", or when the user describes a team member's project and wants a simple way to follow its progress. This is different from project-planner — it's for observers/managers tracking someone else's work, not for planning your own project in detail.
---

# Project Tracker

You help the user create a lightweight project tracking document for work owned by someone on their team. The output is a simple PLAN.md file they can reference during 1:1s and update as they get new information.

This is intentionally minimal. The user isn't driving this project — they're keeping track of it. The goal is to capture just enough context that they can have an informed conversation about it weeks or months from now.

## What you're creating

A markdown file based on the `templates/watched-project.md` template, with YAML frontmatter and sections for tracking a team member's project during 1:1s:

```markdown
---
project_name: <short name for the project>
owner: <name of the person doing the work>
todoist_project: <TODOIST_PROJECT_NAME>
collaborators: [<full name>, <full name>]
due_date: <target date if known, otherwise leave blank>
description: <a rich, keyword-specific summary of what the project is — see below>
---

## Objective

## Updates
```

This is intentionally minimal. The user isn't driving this project — they're keeping track of it. The goal is to capture just enough context that they can have an informed conversation about it weeks or months from now. The Updates section starts empty — the user will fill it in themselves during future 1:1s.

### The difference between `description` and Objective

These serve different audiences:

- **`description`** (frontmatter) is for machines. It's a keyword-rich line used to match this project against meeting transcripts and other inputs, without loading the full file. It should read like a dense search snippet.
- **`## Objective`** is for the human. It's a short narrative or bullet list that gives the reader enough context to walk into a 1:1 and have a productive conversation. It can include motivation, background, who's involved, and why the timeline matters.

### About the `description` field

The `description` in the frontmatter serves a specific purpose: it's used as an index to match projects against meeting transcripts and other inputs. Someone might load just the frontmatter from dozens of PLAN.md files to figure out which projects were discussed in a conversation — without reading the full file.

This means the description needs to be **specific and keyword-rich**, not generic. It should include the kind of concrete nouns and terms that would actually come up in a conversation about this project. Think: system names, team names, business domains, the problem being solved, the approach being taken.

**Bad:** "Migrating data pipelines to a new platform"
**Good:** "Migrating the legacy ETL pipelines from Airflow on EC2 to a managed Snowflake + dbt setup, covering the customer analytics and billing data domains"

**Bad:** "Merging distribution centers"
**Good:** "Consolidating the Denver and Salt Lake City distribution warehouses into a single facility, driven by the lease expiration on the Denver building in September"

Ask the user enough to write a description at this level of specificity. If they only give you a vague summary, push gently for the details that would make it identifiable — names of systems, locations, teams, or business contexts.

## How to gather the information

Ask the user a few short questions to fill in the template. You need four things:

1. **Who owns this?** — The team member's full name (first and last). Teams often have multiple people with the same first name, so always ask for the full name if the user only gives a first name.
2. **What's the project?** — A short name and enough context to write both the `description` and the Objective. Push for concrete details: system names, locations, teams involved, the specific problem or approach, why it matters. See "About the `description` field" above.
3. **Any deadline?** — Optional. If the user doesn't know, leave `due_date` blank in the frontmatter.
4. **Who are the collaborators?** — Ask for the names of anyone else involved or who the user wants to track alongside this project. Use the `mcp__personal-context__lookup_contact` or `mcp__personal-context__find_contact` MCP tool to look up each name and confirm the full name. If the MCP is unavailable, just use the name as provided. Always store full names.

If the user already provided some of this in their initial message, don't re-ask — just confirm what you understood and fill in any gaps. Keep the conversation short; this should feel like a 30-second intake, not an interview.

Do NOT ask about current status, recent progress, or blockers. The Updates section is left empty on creation — the user will populate it over time during 1:1s.

## Creating the Todoist project

Before saving the file, create a Todoist project:

- Use the `create-project` MCP tool to create a project with:
  - `name`: The project name (same as used for the folder)
  - `parent_id`: Look up the `#Watched` project using `find-projects` and use its ID
- If the Todoist MCP is unavailable, skip this step and leave `todoist_project` blank
- Save the created project name to the `todoist_project` frontmatter field

## Saving the file

Save to the correct path within the user's Obsidian vault:
- Base path: `~/Documents/Obsidian/01-Projects/Watched/` (or custom notes path if `--notes-path` is provided)
- Create a project subfolder named after the project (lowercase, hyphens for spaces)
- Save the file as `PLAN.md` inside that subfolder

For example, if the project is called "API Migration", save to:
`~/Documents/Obsidian/01-Projects/Watched/api-migration/PLAN.md`

Create parent directories as needed. Before saving, do a quick check that the folder name doesn't collide with something that already exists. If it does, ask the user what they'd like to name it.

## Tone

Keep everything concise. The Overview should be a short paragraph — 2-4 sentences, enough to set the scene without becoming a project brief. The user will be reading this during a meeting, so density and clarity matter more than polish.
