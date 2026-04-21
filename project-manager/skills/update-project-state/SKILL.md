---
name: update-project-state
description: Updates PLAN.md files based on completed work, meeting transcripts, and general comments. Marks tasks complete, removes obsolete tasks, detects phase completion, and prompts for next-phase planning when a phase wraps up with no task detail ready. Called by /finish-day after day-end processing, or invoked directly when the user says "update my projects", "mark project tasks done", "sync project state", or "project update". Must be run from the root of the Obsidian vault.
---

# Update Project State

You are helping the user keep their project plans current. Given a summary of what was accomplished — completed tasks, meeting outcomes, transcript notes, and general comments — you review each relevant PLAN.md and update it to reflect reality: marking tasks done, removing tasks that are no longer needed, and flagging when a phase has wrapped and the next phase needs planning attention.

## Arguments

- `--projects-path <path>` — override projects folder (default: `01-Projects`)
- `--project <name>` — limit updates to a single named project (default: all active projects)
- `--completed-tasks <text>` — newline- or comma-separated completed Todoist task names (passed by `/finish-day`)
- `--transcript-summary <text>` — transcript processing output from `/exec-assistant:process-transcripts` (passed by `/finish-day`)
- `--comments <text>` — free-form notes, decisions, or context about today's work

## Configuration

If a `CLAUDE.md` exists at the vault root with a **Chief of Staff** config block, path values there are used as defaults — no arguments needed. The precedence for each path is:

1. Per-invocation argument (highest)
2. Value from `CLAUDE.md` Chief of Staff block
3. Hardcoded default

Example `CLAUDE.md` block:

```
## Chief of Staff
- projects-path: Projects
```

## Vault Paths (relative to vault root)

- Projects: resolved `projects-path` (default: `01-Projects/`) — each project is a subfolder containing a `PLAN.md`

---

## Phase 0: Setup

**Resolve vault paths.** Check `CLAUDE.md` at vault root for a "Chief of Staff" section and read `projects-path` if present. Per-invocation arguments override CLAUDE.md values; CLAUDE.md values override hardcoded defaults.

Run via Bash:

```bash
echo "TODAY=$(date +%Y-%m-%d)"
```

Store TODAY for use in Updates entries.

---

## Phase 1: Gather Input Details

Collect the details about what was accomplished. These come from one of two sources:

**When called by `/finish-day`:** The calling skill passes context directly:
- Completed Todoist task names from Phase 1 of finish-day
- Transcript processing summary from `/exec-assistant:process-transcripts` (finish-day Phase 5)
- Any project-related brain dump items noted in finish-day Phase 3

Accept these and move to Phase 2.

**When invoked standalone:** Ask the user:

> "What did you accomplish today? Give me completed tasks, meeting notes, decisions made — anything that reflects work done on your projects. You can be free-form."

Accept free-form input. If the user names specific projects, note them — those will be prioritized for matching. If the user pastes Todoist task names, meeting notes, or a transcript excerpt, treat it all as evidence for matching.

---

## Phase 2: Load Projects and Match Evidence

**Determine scope.** If `--project` was specified, load only that project's PLAN.md. Otherwise, read all `<projects-path>/*/PLAN.md` files. Skip tracked projects (those with only an `## Updates` section and no phases) — they have no task structure to update.

**For each owned project, extract:**
- Project name (frontmatter `name` or `project_name`)
- All phases and their tasks — separately collect open tasks (`- [ ]`) and completed tasks (`- [x]`) per phase
- The active phase — the first phase that still has open (`- [ ]`) tasks
- Later phases — phases with no open tasks yet (intent-only or not yet started)

**Match input details to projects and tasks:**

Work through the completed task names, transcript content, and comments. For each piece of information:

1. **Identify the project.** Match by project name, known keywords, or any tag mentioned. If a piece of evidence doesn't clearly map to any project, skip it — don't guess.

2. **Identify the task.** Within that project's active phase, find the PLAN.md task (`- [ ]` item) that best matches. Use judgment — "Wrote API auth module" maps to "- [ ] Implement API authentication layer"; "Deployed to staging" maps to "- [ ] Stand up staging environment". If no match is clear, skip.

3. **Flag as complete or remove:**
   - **Complete:** Evidence clearly indicates the task was done (task was finished, shipped, merged, delivered)
   - **Remove:** Evidence clearly indicates the task is no longer needed (explicitly dropped, replaced by a different approach, out of scope per a decision made today)
   - **No action:** Ambiguous, partial, or unrelated evidence — leave the task unchanged

**Scope caution on partial completion:** A single completed Todoist task may represent only part of a broader PLAN.md task. Only mark the PLAN.md task complete if the evidence covers the full scope. If unsure, leave it open and note the partial progress in the Updates entry instead.

If no input maps to any project task, say so and exit cleanly:

> "Nothing in today's updates maps to open project tasks. No changes needed."

---

## Phase 3: Present Proposed Changes

Before modifying any files, present a per-project summary for confirmation.

For each project with proposed changes:

```
### [Project Name]
Active phase: Phase N — [Phase objective, one line]

Mark complete:
- [x] Task description  ← based on: "completed auth module" in Todoist
- [x] Task description  ← based on: transcript note re: deployment

Remove (no longer needed):
- ~~Task description~~  ← based on: "we're dropping the manual export" in comments

No change (open, no matching evidence):
- [ ] Task description
- [ ] Task description
```

After showing all projects, ask:

> "Do these look right? Any corrections before I update the plans?"

Accept corrections. If the user adds tasks to the "mark complete" or "remove" list that weren't proposed, include them. If the user rejects a proposed change, drop it. Collect all decisions before proceeding — don't apply changes piecemeal.

---

## Phase 4: Apply Changes to PLAN.md Files

For each project with confirmed changes, use the Edit tool:

**Mark tasks complete:** Change `- [ ]` to `- [x]` for each confirmed task.

**Remove tasks:** Delete the line for each confirmed removal.

**Append an Updates entry** to the `## Updates` section (most recent first). Keep it to 1–3 sentences:

```markdown
- **YYYY-MM-DD:** [What was completed. If tasks were removed, note why. E.g., "Completed auth layer tasks: API auth, token refresh, session management. Dropped manual export task — deferred to v2."]
```

If no Updates section exists yet, add one after the last phase:

```markdown
## Updates

_Most recent entries at top_

- **YYYY-MM-DD:** [Summary]
```

---

## Phase 5: Phase Completion Check

After applying changes, check each modified project for phase completion.

**A phase is complete when** all tasks in it are `- [x]` — no `- [ ]` items remain.

For each completed phase, examine the next phase:

**Next phase has concrete tasks** (`- [ ]` items exist): The project is moving forward. Note it:

> "Phase N complete → Phase N+1 is ready with [X] open tasks."

**Next phase has no tasks** (objective and prose only, no `- [ ]` items): This is a planning gap. The phase wrapped but there's nothing to pick up next.

Surface this to the user:

```
⚠️  [Project Name] — Phase N is complete, but Phase N+1 needs planning detail.

Phase N+1 objective: [Objective from PLAN.md]
Open questions noted in the plan: [List from plan, or "none documented"]

Suggested milestones for Phase N+1:
1. [Boulder 1 — derived from the project's domain and Phase N+1 objective]
2. [Boulder 2]
3. [Boulder 3]
4. [Boulder 4 — optional, only if clearly warranted]

These are the major chunks — you know the tactical steps better than I do.
Want to flesh out Phase N+1 now, or come back to it?
```

Milestone suggestions must be grounded in the project's actual context (domain, team, known constraints from the plan) — not generic placeholders. Four milestones is usually right; three is fine for simpler phases; five is the max.

**If the user wants to plan now:** Invoke `/project-manager:project-planner`. The planner's "Revisiting and Refining the Plan" mode handles the interview and document update.

**If the user defers:** Append a note to the Updates entry already written for this project:

```
Phase N+1 planning deferred — needs task detail before work can begin.
```

---

## Phase 6: Closing Summary

Present a clean summary of all changes made:

```
Project state updated.

[Project Name]
  Marked complete: N tasks in Phase X
  Removed: N tasks
  Phase X complete → Phase X+1 [ready with N open tasks / needs planning]

[Project Name 2]
  Marked complete: N tasks in Phase X

No changes: [Project Name 3], [Project Name 4]
```

If called from `/finish-day`, keep this summary brief — the user is at the end of a long workflow. Return control to finish-day after the summary without additional prompts.

---

## Quality Notes

- Require clear evidence before marking anything complete or removed — don't infer from vague signals
- Partial work (one Todoist task done out of several implied by a PLAN.md item) does not make the PLAN.md task complete; note the partial progress in the Updates entry instead
- Only propose removal when the input explicitly indicates a task is being dropped — not just because it wasn't mentioned today
- Always confirm before writing; never apply changes speculatively
- Phase completion is a significant event — make the Updates entry reflect that concretely
- Milestone suggestions for next-phase planning should use the project's actual domain language; never output generic boilerplate like "Define requirements" or "Conduct testing"
- When called from finish-day, minimize back-and-forth: batch all project decisions into one confirmation round and keep summaries tight
