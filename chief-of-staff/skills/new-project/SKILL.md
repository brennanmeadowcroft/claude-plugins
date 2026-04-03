---
name: new-project
description: Create a new project — Obsidian folder and PLAN.md (via /project-planner for your own projects, or /project-tracker for team member projects), plus a matching Todoist project in the right location. Trigger on phrases like "create a new project", "start a new project", "set up a project", "add a project", or when the user wants to kick off something new and needs both a planning document and a Todoist project created together.
---

# New Project

You help the user create a new project: a folder in their Obsidian vault and a matching Todoist project. Once the project is set up, you hand off to the right skill to generate the PLAN.md.

## Arguments

- `--projects-path <path>` — override the projects root folder. Takes precedence over any CLAUDE.md config. Default: `01-Projects`.

## Configuration

If a `CLAUDE.md` exists at the vault root with a **Chief of Staff** config block, the `projects-path` value there is used as the default — no argument needed. The precedence is:

1. `--projects-path` argument (highest)
2. `projects-path` in `CLAUDE.md` chief-of-staff config block
3. Hardcoded default: `01-Projects`

Example `CLAUDE.md` block:

```
## Chief of Staff
- projects-path: Projects
```

---

## Phase 0: Gather Project Info

**First, resolve the projects path.** Check `CLAUDE.md` at vault root for a "Chief of Staff" section and read the `projects-path` value if present. If `--projects-path` was passed, it overrides the CLAUDE.md value. If neither is set, use `01-Projects`.

Then ask the user two questions (they can answer both at once):

1. **Project name** — what's this project called?
2. **Ownership** — is this _your_ project, or are you tracking it for someone on your team?
   - _Mine_ → full project plan via `/project-planner`, saved to `<projects-path>/<slug>/`
   - _Team member's_ → lightweight tracker via `/project-tracker`, saved to `<projects-path>/Watched/<slug>/`

Derive a `slug` from the project name: lowercase, spaces to hyphens, strip special characters (e.g., "API Migration" → `api-migration`).

---

## Phase 1: Confirm Location

Tell the user where things will go before acting:

- **Obsidian folder:** `<projects-path>/<project-name>/` (own) or `<projects-path>/Watched/<project-name>/` (team member's)
- **Todoist project:** under the matching parent project in Todoist (see Phase 2)

Check that the target folder doesn't already exist. If it does, ask the user whether to continue (they may be setting up a Todoist project for something that already has a folder).

---

## Phase 2: Create Todoist Project

Use the Todoist MCP to find the right parent project, then create the new project under it.

**Step 1 — Find the parent project:**

Call `get-projects` (or equivalent list tool) to fetch all projects. Search for a project whose name matches the projects root:

- For own projects: projects should be nested under "#Parsyl", or a close variant
- For team member's projects: should be nested under "#Watched" or a close variant

If no matching parent is found, create the Todoist project at the top level and note that the user may want to move it manually.

**Step 2 — Create the project:**

Call `create-project` with:

- `name`: the project name (not the slug — use the display name)
- `parent_id`: ID of the parent project found above (omit if top-level)

Tell the user: "Created Todoist project **[name]**" and note the parent it was placed under.

**If the Todoist MCP doesn't expose project management tools**, fall back to the Todoist REST API v1:

```
POST https://api.todoist.com/api/v1/projects
Authorization: Bearer <token>
Content-Type: application/json

{ "name": "<project name>", "parent_id": "<parent_id>" }
```

The API returns a project object — capture the `id` for reference.

> **API note:** Todoist API v1 response shape wraps lists in a named object key (e.g., `{ results: [...] }`). When fetching all projects, check the top-level key whose value is an array.

---

## Phase 3: Hand Off to Planning Skill

Once the Todoist project is created, invoke the appropriate skill. Pass the project name and target save path as context so the skill doesn't need to re-ask.

**Own project → `/project-planner`**

Say:

> "Todoist project created. Now let's build out the plan — I'll run /project-planner for you."
> "When it asks where to save, the target path is `<projects-path>/<slug>/PLAN.md`."

Then invoke `/project-planner`. It will interview the user and write the PLAN.md. Remind it (in your handoff context) to save the file at `<projects-path>/<slug>/PLAN.md`.

**Team member's project → `/project-tracker`**

Say:

> "Todoist project created. Let me set up the tracker now — I'll run /project-tracker for you."

Then invoke `/project-tracker`. Remind it (in your handoff context) to save the file at `<projects-path>/Watched/<slug>/PLAN.md` — not the default `Watched/<slug>/PLAN.md`, since we're placing it under the configured projects path.
