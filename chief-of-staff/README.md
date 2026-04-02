# Chief of Staff

AI-enabled executive assistant for Claude Code. Seven skills that work together to keep you deliberate about your time, on top of your projects, and moving purposefully through each day and week.

**The problem it solves:** Knowledge work is full of context-switching, accumulating commitments, and slow entropy — tasks slip, projects drift, and weeks end without a clear sense of what moved forward. Chief of Staff gives you a structured rhythm: open the week with intention, start each day with a real briefing, close the day cleanly, review the week honestly, and keep your projects from becoming a graveyard of half-finished plans.

---

## How the Skills Work Together

The skills form an integrated operating cycle:

```
Monday morning     → /start-week    Set 2–3 priorities, surface project deadlines, create the weekly file
Each morning       → /start-day     Briefing: calendar, priority emails, weekly priorities, tasks, meeting notes
Throughout week    → /project-index Quick project status lookup (also called automatically by other skills)
Throughout week    → /project-planner  Turn a new initiative into a structured, phased plan
Throughout week    → /project-tracker  Lightweight tracking for projects owned by your team
Each evening       → /finish-day    Close out: email triage, brain dump, reschedule, prep tomorrow's notes
Friday afternoon   → /wrap-week     Narrative recap fills in the weekly file /start-week created
```

The daily rhythm is the foundation: `/finish-day` each evening seeds the context that makes `/start-day` valuable the next morning. The weekly rhythm gives that daily context meaning — priorities set on Monday shape how you rank tasks and allocate focus all week. The project skills connect the big picture (multi-week initiatives) to the daily and weekly ground level.

---

## Prerequisites

All skills require MCP servers for calendar, tasks, email, and vault access. Set them up once and they persist in your Claude Code user config.

### 1. Todoist (Official Hosted MCP)

```bash
claude mcp add --transport http todoist https://ai.todoist.net/mcp --scope user
```

Then authenticate inside Claude Code:
```
/mcp
```
Select "todoist" and complete the OAuth flow in your browser.

### 2. Google Calendar

**Step 1:** Create a Google Cloud project and enable the Google Calendar API.
Follow the authentication guide at: https://github.com/nspady/google-calendar-mcp#authentication

Download your OAuth credentials JSON file (e.g., to `~/gcp-oauth.keys.json`).

**Step 2:** Register the MCP server:
```bash
claude mcp add --transport stdio \
  --env GOOGLE_OAUTH_CREDENTIALS=$HOME/gcp-oauth.keys.json \
  google-calendar --scope user \
  -- npx -y @cocal/google-calendar-mcp
```

The first time Claude Code uses this server it will open a browser for OAuth consent.

### 3. Gmail

`/start-day` and `/finish-day` check for unread emails labeled `Priority/p1` or `Priority/p2`. Any Gmail MCP server that supports label-based search works. One option using the community `@gptscript-ai/gmail-mcp` server:

```bash
claude mcp add --transport stdio \
  --env GOOGLE_OAUTH_CREDENTIALS=$HOME/gcp-oauth.keys.json \
  gmail --scope user \
  -- npx -y @gptscript-ai/gmail-mcp
```

Set up `Priority/p1` and `Priority/p2` labels in Gmail and apply them to emails that need your attention. The skills search for `label:Priority/p1 OR label:Priority/p2 is:unread` — adjust the query format to match your MCP server's API.

If Gmail MCP is unavailable, both skills degrade gracefully and note that email data was skipped.

### 4. Obsidian (mcpvault — filesystem direct)

No Obsidian plugins required. Works even when Obsidian is closed.

```bash
claude mcp add --transport stdio \
  --env VAULT_PATH=/path/to/your/vault \
  obsidian --scope user \
  -- npx -y mcpvault
```

Replace `/path/to/your/vault` with the absolute path to your Obsidian vault (e.g., `/Users/yourname/Documents/MyVault`).

---

## Obsidian Vault Setup

Enable the **Daily Notes** core plugin in Obsidian (Settings → Core Plugins → Daily Notes):
- Folder: `Daily Notes`
- Date format: `YYYY-MM-DD`
- Template: optional — `/start-day` will create notes with its own template

The skills assume this folder structure in your vault:

```
vault/
├── 01-Projects/            ← one subfolder per project, each with a PLAN.md
│   ├── my-project/
│   │   └── PLAN.md
│   └── ...
├── 02-AreasOfResponsibility/
│   ├── Daily Notes/        ← lightweight day hubs (created by /start-day)
│   │   ├── 2026-03-30.md
│   │   └── ...
│   ├── Notes/              ← your existing meeting notes (untouched)
│   │   ├── 1:1 with Alex.md
│   │   ├── Team Standup.md
│   │   └── ...
│   └── Weekly Recaps/      ← narrative weekly summaries (created by /wrap-week)
│       ├── 2026-W13.md
│       └── ...
└── Watched/                ← project tracker docs (created by /project-tracker)
    └── some-project/
        └── PLAN.md
```

Your existing `Notes/` folder is never modified except to append new date sections by `/finish-day`. No content is moved or duplicated.

Override the default paths with arguments if your vault uses different folder names:
```
/start-day --daily-notes-path "Journal/Daily" --notes-path "Meetings"
/wrap-week --weekly-recaps-path "Reviews/Weekly"
```

---

## Transcript Workflow

By default, `/finish-day` shows a checklist reminder to download transcripts and drop them in your n8n pickup folder.

To automate the trigger, expose your n8n webhook as a single-tool MCP server. A minimal implementation using the MCP SDK:

```javascript
// n8n-mcp/index.js
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new McpServer({ name: "n8n", version: "1.0.0" });

server.tool("trigger_transcript_processing", "Trigger n8n transcript workflow", {}, async () => {
  await fetch(process.env.N8N_WEBHOOK_URL, { method: "POST" });
  return { content: [{ type: "text", text: "Transcript processing triggered." }] };
});

await server.connect(new StdioServerTransport());
```

Register it:
```bash
claude mcp add --transport stdio \
  --env N8N_WEBHOOK_URL=https://your-n8n-instance/webhook/transcripts \
  n8n --scope user \
  -- node /path/to/n8n-mcp/index.js
```

Then pass the server name to finish-day:
```
/finish-day --transcript-mcp n8n
```

---

## Skills Reference

| Skill | Description | When to use |
|---|---|---|
| `/start-week` | Set 2–3 weekly priorities, review projects for deadlines, create weekly planning file | Monday morning |
| `/start-day` | Morning briefing with priority emails, weekly priorities, calendar, tasks, and meeting notes | Each morning before starting work |
| `/finish-day` | Day close-out: priority email triage, brain dump, reschedule tasks, transcript reminder, prep tomorrow's notes | Each evening before logging off |
| `/wrap-week` | Mon–Sun narrative recap saved to Obsidian, fills in the weekly planning file, reviews areas of responsibility | Friday afternoon or Sunday evening |
| `/project-index` | Fast lookup of all active projects — names, descriptions, areas, due dates from PLAN.md frontmatter | On demand, or automatically by other skills |
| `/project-planner` | Turn a new initiative into a structured, phased plan with objectives, tasks, and exit criteria | When starting or updating a project you own |
| `/project-tracker` | Lightweight tracking doc for a project owned by someone on your team | When you need to follow a report's project during 1:1s |

### Arguments

**`/start-week`**
- `--weekly-recaps-path <path>` — Override weekly recaps folder (default: `02-AreasOfResponsibility/Weekly Recaps`)

**`/start-day`**
- `--daily-notes-path <path>` — Override default daily notes folder (default: `02-AreasOfResponsibility/Daily Notes`)
- `--notes-path <path>` — Override meeting notes folder (default: `02-AreasOfResponsibility/Notes`)

**`/finish-day`**
- `--daily-notes-path <path>` — Override default daily notes folder
- `--notes-path <path>` — Override meeting notes folder
- `--transcript-mcp <server-name>` — Name of an MCP server to trigger for transcript processing

**`/wrap-week`**
- `--daily-notes-path <path>` — Override default daily notes folder
- `--weekly-recaps-path <path>` — Override weekly recaps folder (default: `02-AreasOfResponsibility/Weekly Recaps`)
- `--areas-path <path>` — Override areas of responsibility root folder (default: `02-AreasOfResponsibility`)

**`/project-index`**
- No arguments — reads from `01-Projects/*/PLAN.md` in the current working directory

**`/project-planner`**
- No arguments — begins an interview to scope and structure the project

**`/project-tracker`**
- No arguments — begins a short intake to create a lightweight tracker

---

## Tips

**Run the full cycle for the first two weeks.** The skills get meaningfully richer when they can read context from each other. `/start-day` reads the weekly priorities `/start-week` set. `/wrap-week` reads the daily notes `/start-day` and `/finish-day` wrote. The first week feels lighter; by week three it feels like a real operating system.

**Daily note as a hub.** Keep meeting content in your long-running `Notes/` files. Daily notes link to those notes and capture your intentions and reflections — no duplication.

**Todoist priority discipline.** The morning briefing ranks tasks by p1/p2. If everything is p1, the ranking loses meaning. Consider a personal rule: max 2–3 p1 tasks at any time.

**Calendar blocking.** Block deep-work time as private Google Calendar events. `/start-day` will include those blocks when suggesting focus windows, making the suggestion more useful.

**Weekly recap as a personal changelog.** ISO week filenames (`2026-W13.md`) sort naturally and are easy to review during quarterly or annual reflections.

**Run `/finish-day` before leaving for the day** — not after. The meeting note prep for tomorrow works best when done while context is fresh.

**Project descriptions are for machines.** The `description` field in each `PLAN.md` is read by the hook and injected as context into `/start-week` and other skills. Write it like a dense search snippet — system names, team names, the specific problem — so the index is useful for matching.

**`/project-tracker` vs. `/project-planner`.** Tracker is for watching someone else's work (your reports, cross-functional partners). Planner is for structuring work you own. Don't use planner for observation — it'll create false accountability.
