---
name: exec-monitor
description: "Poll Todoist for tasks labelled @claude, dispatch specialized agents to complete them, and deliver results back. Use when running the exec-assistant task monitor — manually or via scheduled cron. Trigger on: 'run exec monitor', 'check for Claude tasks', 'check my assigned tasks'."
argument-hint: "[--dry-run] [--notes-path <vault-root>]"
allowed-tools: Task, Bash, Read, Write
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

## Phase 3.5 — Resolve project names

Call `find-projects` to get the full project list. Build a lookup map of `project_id → project_name`.

For each claimed task, look up the project name using the task's `project_id`. This is used to determine the output path for research results:
- Path: `{notes-path}/01-Projects/{project-name}/Notes/`
- If the task has no project or the project can't be found, use `{notes-path}/01-Projects/Claude Tasks/Notes/`

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

**Dispatch each task** using the Task tool with the appropriate agent. Pass:
```
Task content: {task.content}
Task description: {task.description}
Task ID: {task.id}
Project: {project-name}
Output path (if research): {resolved-output-path}
Labels: {task.labels}

Complete this task and return a JSON result in this exact format:
{
  "type": "update" | "research" | "notification",
  "summary": "1-2 sentence summary of what was done",
  "body": "full markdown content (only for type=research)",
  "notification": "short message for desktop notification (only for type=notification)"
}
```

Dispatch tasks in parallel where possible. Collect all results before proceeding to Phase 5.

---

## Phase 5 — Deliver results

For each completed agent dispatch, handle the result based on `type`:

**`type: "update"`**
- Call `add-comments` with the result summary
- Call `complete-tasks`

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
- Call `complete-tasks`

**`type: "notification"`**
- Fire desktop notification: `osascript -e 'display notification "{notification}" with title "Exec Assistant"'`
- Call `add-comments` with the summary
- Call `complete-tasks`

**On agent error / unexpected result**
- Reset the task: call `update-tasks` to swap `claude-doing` back to `claude` in labels
- Call `add-comments` with: `Agent failed. Task reset for retry. Error: {error-details}`
- Fire desktop notification: `osascript -e 'display notification "Task failed and was reset: {task-content}" with title "Exec Monitor ⚠️"'`

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
