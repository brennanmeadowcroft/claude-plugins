# Exec Assistant

Autonomous Todoist task monitor for Claude Code. Polls for tasks labelled `@claude`, dispatches the right agent to complete them, and delivers results back — without interrupting you.

**The problem it solves:** Delegating work to Claude shouldn't require an open conversation. Exec Assistant lets you assign tasks to Claude directly in Todoist and have them completed in the background, with results written to your Obsidian vault or posted back as task comments.

---

## How It Works

1. Label any Todoist task with `@claude`
2. Run `/exec-monitor` (or schedule it via `/schedule`)
3. The monitor claims each task, routes it to the right agent, and delivers the result:
   - **Research tasks** → written to your Obsidian vault as a note
   - **General tasks** → result posted as a Todoist comment, task completed
   - **Notifications** → desktop notification fired, task completed

### Task Routing

The monitor infers the right agent from the task content, or you can route explicitly with a label:

| Label | Agent |
|---|---|
| `agent:research` | Research agent — multi-source web research |
| `agent:schedule` | Schedule agent — calendar and scheduling tasks |
| *(none)* | Inferred from task content |

---

## Prerequisites

### Todoist MCP Server

Register the official Todoist MCP server globally in Claude Code:

```bash
claude mcp add --transport http --scope global todoist https://ai.todoist.net/mcp
```

Claude Code will prompt you to authenticate with Todoist the first time a tool is called.

---

## Usage

### Manual run

```
/exec-monitor
```

### Dry run (see pending tasks without claiming them)

```
/exec-monitor --dry-run
```

### With a custom Obsidian vault path

```
/exec-monitor --notes-path ~/Documents/MyVault
```

The default notes path is `~/Documents/Obsidian`. Research results are written to:
```
{notes-path}/01-Projects/{project-name}/Notes/{task-slug}.md
```

### Scheduled

To run automatically on a schedule, use the `/schedule` skill:

```
/schedule exec-monitor every 30 minutes
```

---

## Stale Task Recovery

If a task gets stuck in `@claude-doing` for more than 4 hours (e.g. the agent crashed), the monitor automatically resets it back to `@claude` so it will be picked up on the next run.
