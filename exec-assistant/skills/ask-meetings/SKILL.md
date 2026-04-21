---
name: ask-meetings
description: Query the meeting memory vector store to answer questions about past meetings. Surfaces themes from 1:1s, project status from meeting history, or answers general questions about what was discussed. Must be run from the vault root.
argument-hint: "<natural language question>"
allowed-tools: Bash, Read, Glob
---

# Ask Meetings

Answer questions about past meetings using the meeting memory vector store. Combines semantic search of indexed meeting notes with supplementary context from project plans and tasks where relevant.

## Step 1: Determine query mode

Classify the question into one of three modes before running any searches:

**Mode A — 1:1 themes**
Triggered by questions about: patterns in employee conversations, how someone is doing, recurring topics across 1:1s, team morale, or "this week's 1:1s".
Examples: "What were the key themes in my 1:1s this week?", "What has Craig been focused on?", "How is the team feeling about the roadmap?"

**Mode B — Project status**
Triggered by questions that name a specific project and ask about its current state, recent progress, or blockers.
Examples: "What's the status of [project]?", "What did we discuss about [project] recently?", "Any blockers on [project]?"

**Mode C — General search**
Everything else: decisions made, context on a specific topic, things discussed in a particular meeting, action items, etc.

---

## Step 2: Build and run the query

### Mode A — 1:1 themes

```bash
python3.13 .claude/skills/ask-meetings/scripts/query_meetings.py \
  --meeting-type "1:1" \
  --from-date <YYYY-MM-DD> \
  --to-date <YYYY-MM-DD> \
  --top-k 15 \
  "<the user's question>"
```

- Default date range: last 7 days (use today's date from `date +%Y-%m-%d`)
- If the user specifies a timeframe (e.g. "this month"), adjust the date range accordingly
- If asking about a specific person, add `--project` is not needed; include the person's name in the question text

### Mode B — Project status

First, identify the project slug:
1. Glob `01-Projects/` to see project folder names
2. Match the project name from the question to the closest folder name

Then run two queries in parallel:

**Query 1 — meeting history for this project:**
```bash
python3.13 .claude/skills/ask-meetings/scripts/query_meetings.py \
  --project "<project-slug>" \
  --top-k 10 \
  "<the user's question>"
```

**Query 2 — read the project plan (if it exists):**
```bash
# Check for PLAN.md in the project folder
```
Use Read to load `01-Projects/<project-slug>/PLAN.md` if it exists.

After both queries, also fetch open Todoist tasks for the project using the `list-tasks` MCP tool or the Todoist API, filtering by the project name.

### Mode C — General search

```bash
python3.13 .claude/skills/ask-meetings/scripts/query_meetings.py \
  --top-k 10 \
  "<the user's question>"
```

No filters — broad semantic search across all indexed meetings.

---

## Step 3: Synthesize and present results

Parse the JSON output from the query script. If `status` is `"error"` or `"empty"`, report the issue clearly and stop.

### Mode A — 1:1 themes synthesis

Present findings organized by theme, not by person (unless the question was person-specific). For each theme:
- State the theme clearly
- Name which meetings surfaced it (with dates)
- Include a brief supporting quote or detail from the indexed text

Format:
```
### Key themes across 1:1s (Apr 11–17)

**Theme: Roadmap clarity**
Came up in: Craig Swank (Apr 15), Alex Tran (Apr 14)
> "Concern about Q3 scope — team is unsure which features are committed vs. stretch..."

**Theme: Hiring pipeline**
...
```

Close with: "Source notes: [[Craig Swank - 2026]] · [[Alex Tran - 2026]]" as Obsidian wikilinks using `source_file` from results.

### Mode B — Project status synthesis

Present a structured status update combining all three sources:

```
## [Project Name] — Status as of <date>

### Plan
<2-3 sentence summary of the PLAN.md objective and current phase, if plan exists>

### Recent meeting activity
<Summary of what came up in meetings, with dates and meeting names>

### Open tasks
<Bulleted list of open Todoist tasks, if any>

### Assessment
<1-2 sentence synthesis: is this on track, what needs attention?>
```

If no meeting history was found for the project, say so explicitly.

### Mode C — General search synthesis

Present a direct answer to the question with supporting excerpts. Group results by meeting when multiple chunks from the same meeting appear. Include the meeting name, date, and source file as an Obsidian wikilink for each result.

---

## Notes

- Always include Obsidian wikilinks (`[[filename without .md]]`) so the user can navigate to source notes
- If the store returns 0 results for a filtered query, broaden the search (e.g. remove date range) and mention it
- If `.meeting-memory/` does not exist, tell the user to run `/init-meeting-memory` first
