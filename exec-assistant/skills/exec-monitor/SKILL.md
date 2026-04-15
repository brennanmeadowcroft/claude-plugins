---
name: exec-monitor
description: "Poll Todoist for tasks labelled @claude, dispatch specialized agents to complete them, and deliver results back. Use when running the exec-assistant task monitor — manually or via scheduled cron. Trigger on: 'run exec monitor', 'check for Claude tasks', 'check my assigned tasks'."
argument-hint: "[--dry-run] [--notes-path <vault-root>]"
allowed-tools: Task, Bash, Read, Write, Skill
---

# Exec Assistant Task Monitor

You are the exec-assistant task monitor. Your job is to check Todoist for tasks assigned to Claude, dispatch the right agent for each task, and deliver results back — all without interrupting the user.

## Arguments

- `--dry-run` — List pending tasks without claiming or dispatching. Safe for testing.
- `--notes-path <path>` — Root of the Obsidian vault (default: `~/Documents/Obsidian`). Used to write research output files.

Parse these from the user's message or the arguments passed to this skill.

---

## Phase 0 — Verify MCP connectivity

Call `find-tasks` with `filter: "today"` as a smoke test.

If the call fails or the todoist MCP tool is unavailable:
- Fire a desktop notification: `osascript -e 'display notification "Todoist MCP is not available. Re-run: claude mcp add --transport http todoist https://ai.todoist.net/mcp" with title "Exec Monitor ⚠️"'`
- Print a clear error and stop. Do not proceed.

---

## Phase 1 — Stale task recovery

Call `find-tasks` with `filter: "@claude-doing"`.

For each task returned, check its `updated_at` timestamp. If the task has been in `claude-doing` state for **more than 4 hours**:
- Update the task labels: remove `claude-doing`, add back `claude` (preserve all other labels)
- This resets stale/abandoned claims so they'll be picked up again

---

## Phase 2 — Poll for pending tasks

Call `find-tasks` with `filter: "@claude & !@claude-doing & !@claude-done"`.

If zero tasks are returned:
- Print: "No pending Claude tasks found."
- Stop here.

If `--dry-run` is set:
- List the tasks with their content, project, labels, and description
- Print: "Dry run — no tasks claimed."
- Stop here.

---

## Phase 3 — Claim tasks

For each pending task, atomically claim it by calling `update-tasks`:
- Set `labels` to the task's current labels with `claude` replaced by `claude-doing`
- Preserve all other labels (including any `agent:*` routing labels)

If the update fails for a task, skip it and log a warning — do not dispatch an agent for an unclaimed task.

---

## Phase 3.5 — Resolve project names and output paths

Call `find-projects` to get the full project list. Build a lookup map of `project_id → project_name` and include the `parent_id` for each project.

For each claimed task, determine the output path for research results:
- **If `project_id` is null** → AoR path: `{notes-path}/02-AreasOfResponsibility/Notes/`
- **If the project has `parent_id === null` AND name is "Ongoing"** → AoR path: `{notes-path}/02-AreasOfResponsibility/Notes/`
- **Otherwise** → Project path: `{notes-path}/01-Projects/{project-name}/Notes/`
- **Fallback** (project not found): `{notes-path}/01-Projects/Claude Tasks/Notes/`

Store the resolved output path with each task for use in Phase 4 and Phase 5.

---

## Phase 3.6 — Check for deep-research availability

Attempt to determine if the `deep-research` skill is available by checking if the `research-toolkit` plugin is installed. You can test this with:

```bash
ls ~/.claude/plugins/research-toolkit/skills/deep-research/SKILL.md 2>/dev/null && echo "available" || echo "unavailable"
```

Set a session flag `deep_research_available` to `true` or `false` based on the result. This flag is used in Phase 4 to route research tasks.

---

## Phase 3.75 — Detect RAPID requirements

For each claimed task, check whether the task content or description indicates a RAPID decision document is required. Look for explicit indicators like:
- "RAPID", "decision doc", "decision document", "rapid framework", "recommend approve perform"
- The phrase "requires a RAPID" or "create a RAPID"

If a RAPID is required:
- Set a flag `rapid_required: true` on the task context
- Read the RAPID template from `templates/RAPID.md` (relative to this skill file, located at `exec-assistant/skills/exec-monitor/templates/RAPID.md`)
- Store the template content with the task context for use in Phase 4

---

## Phase 4 — Select and dispatch agents

For each claimed task, determine which agent to use:

**Routing priority:**
1. Task has label `agent:research` → use `task-research-agent`
2. Task has label `agent:schedule` → use `task-schedule-agent`
3. No agent label → **infer from task content and description**:
   - Research indicators: contains words like "research", "find out", "look up", "investigate", "summarize", "what is", "what are", "compare", "analysis" → use `task-research-agent`
   - Scheduling indicators: contains words like "schedule", "book", "set up a meeting", "calendar", "reschedule", "block time", "remind" → use `task-schedule-agent`
   - Unclear or general → use `task-general-agent`

**Dispatch each task:**

For research tasks (`task-research-agent` would normally handle these):
- **If `deep_research_available` is true**: Use the `Skill` tool to invoke `deep-research` with the task content and description as the argument (format: `"{task.content}: {task.description}"`). Collect the output and format it as a research result. Then return:
  ```json
  {
    "type": "research",
    "summary": "Deep research completed on: {task.content}",
    "body": "{full output from deep-research skill}"
  }
  ```
- **If `deep_research_available` is false**: Use the Task tool to dispatch `task-research-agent` as normal.

For other tasks (schedule, general), use the Task tool with the appropriate agent. Pass:
```
Task content: {task.content}
Task description: {task.description}
Task ID: {task.id}
Project: {project-name}
Output path (if research): {resolved-output-path}
Labels: {task.labels}
RAPID Required: {rapid_required | false}
RAPID Template: {rapid_template_content | ""}

Complete this task and return a JSON result in this exact format:
{
  "type": "update" | "research" | "notification",
  "summary": "1-2 sentence summary of what was done",
  "body": "full markdown content (only for type=research)",
  "notification": "short message for desktop notification (only for type=notification)"
}
```

If `RAPID Required` is true, the agent should use the RAPID template as the structure for its output instead of the standard research findings format. Fill in all sections of the RAPID with the research findings. Leave names blank unless provided in the task content or description.

Dispatch tasks in parallel where possible. Collect all results before proceeding to Phase 5.

---

## Phase 5 — Deliver results

For each completed agent dispatch, handle the result based on `type`:

**`type: "update"`**
- Call `add-comments` with the result summary
- Call `complete-tasks` with labels updated to add `claude-done` (remove `claude-doing`)

**`type: "research"`**
- Determine the output file path: `{output-path}/{slug}.md` where slug is a kebab-case version of the task content (e.g., "Research MCP adoption" → `research-mcp-adoption.md`)
- Build the Todoist task URL: `https://app.todoist.com/app/task/{kebab-case-task-content}-{task.id}` (e.g., task "Research MCP adoption" with id `abc123` → `https://app.todoist.com/app/task/research-mcp-adoption-abc123`)
- Prepend a task link header to the body before writing:
  ```
  > [View in Todoist](https://app.todoist.com/app/task/{slug}-{task.id})

  {body}
  ```
- Write the combined content to that file using the Write tool. Create parent directories if needed.
- Call `add-comments` with: `Result saved to: {relative-vault-path}\n\n{summary}`
- Call `complete-tasks` with labels updated to add `claude-done` (remove `claude-doing`)

**`type: "notification"`**
- Fire desktop notification: `osascript -e 'display notification "{notification}" with title "Exec Assistant"'`
- Call `add-comments` with the summary
- Call `complete-tasks` with labels updated to add `claude-done` (remove `claude-doing`)

**On agent error / unexpected result**
- Reset the task: call `update-tasks` to swap `claude-doing` back to `claude` in labels
- Call `add-comments` with: `Agent failed. Task reset for retry. Error: {error-details}`
- Fire desktop notification: `osascript -e 'display notification "Task failed and was reset: {task-content}" with title "Exec Monitor ⚠️"'`

---

## Phase 6.5 — Write AI Actions to daily note

For all successfully completed tasks (all types: update, research, notification):

1. Get today's date via bash: `date +%Y-%m-%d`
2. Construct the daily note path: `{notes-path}/02-AreasOfResponsibility/Daily Notes/{YYYY-MM-DD}.md`
3. Read the file if it exists. If it doesn't exist, start with an empty string.
4. Check if the file contains a `## AI Actions` heading. If not, append it to the file content.
5. For each completed task, append a bullet point in this format:
   ```
   - Completed "[task content]" — [brief result summary]. [View in Todoist](https://app.todoist.com/app/task/{slug}-{task.id})
   ```
   where `slug` is the kebab-case version of the task content and `task.id` is the task ID.
6. Write the updated content back to the daily note file. Create parent directories if needed.

---

## Phase 6 — Summary

Print a summary:
```
Exec monitor run complete.
  Pending tasks found: X
  Tasks claimed: X
  Dispatched: X (research: N, schedule: N, general: N)
  Completed: X
  Failed/reset: X
  Stale tasks recovered: X
```
