# Exec Assistant

Executive assistant layer for Claude Code. Handles meeting lifecycle, email prioritization, and autonomous background task processing — so you can focus on the work that needs you.

**Two modes of operation:**
- **On-demand skills** — invoked by you or by chief-of-staff during daily/weekly flows (meeting prep, transcript processing, email prioritization)
- **Autonomous monitor** — polls Todoist for tasks labelled `@claude` and dispatches agents to complete them in the background

---

## Skills

### Meeting Lifecycle

| Skill | Description | When to use |
|-------|-------------|-------------|
| `/exec-assistant:meeting-prep` | Pre-meeting brief — agenda, talking points, attendee context, prior notes | Before any meeting |
| `/exec-assistant:process-transcripts` | Process transcripts into structured notes and Todoist action items | After meetings |
| `/exec-assistant:ask-meetings` | Query meeting memory to surface past decisions, themes, history | Any time |
| `/exec-assistant:index-meeting-note` | Manually index a meeting note into the vector store | Backfilling |
| `/exec-assistant:init-meeting-memory` | One-time setup of ChromaDB meeting memory store | First-time setup |

### Email

| Skill | Description | When to use |
|-------|-------------|-------------|
| `/exec-assistant:email-prioritization` | Label Gmail messages p1–p5 so chief-of-staff surfaces the right ones | Before `/start-day` or on schedule |

### Background Task Monitor

| Skill | Description | When to use |
|-------|-------------|-------------|
| `/exec-assistant:exec-monitor` | Poll Todoist for `@claude` tasks and dispatch agents | On demand or scheduled |

---

## Autonomous Task Monitor

The exec-monitor skill polls Todoist for tasks with the `@claude` label, claims them, routes to the right agent, and delivers results — without interrupting you.

**How to assign a task:**
1. Label any Todoist task with `@claude`
2. Run `/exec-monitor` or schedule it with `/schedule`
3. Results are written to your Obsidian vault or posted as task comments

### Task Routing

| Label | Agent |
|-------|-------|
| `agent:research` | Research agent — multi-source web research |
| `agent:schedule` | Schedule agent — calendar and scheduling tasks |
| *(none)* | Inferred from task content |

### Using for Delegated Drafts

When `/finish-day` surfaces email drafting candidates, it creates Todoist tasks with `@claude` label containing the email details (subject, sender, Gmail link, action). Exec-monitor picks these up on the next run and routes to the general agent, which drafts the response. Review the draft and send — no extra steps needed.

### Stale Task Recovery

Tasks stuck in `@claude-doing` for more than 4 hours are automatically reset to `@claude` on the next run.

---

## Scheduled Operation

```
/schedule exec-monitor every 30 minutes
```

---

## Prerequisites

### Todoist MCP Server

```bash
claude mcp add --transport http --scope global todoist https://ai.todoist.net/mcp
```

### Meeting Memory (one-time setup)

Run once from your Obsidian vault root:

```
/exec-assistant:init-meeting-memory
```

---

## Usage Examples

```
/exec-assistant:meeting-prep --meeting "1:1 with Alex" --date 2026-04-21
/exec-assistant:process-transcripts
/exec-assistant:ask-meetings what did we decide about the API redesign?
/exec-assistant:email-prioritization
/exec-monitor
/exec-monitor --dry-run
/exec-monitor --notes-path ~/Documents/MyVault
```
