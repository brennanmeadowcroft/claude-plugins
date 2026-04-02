---
name: start-week
description: Weekly planning session — reviews projects for due dates and open work, guides the user to set 2–3 priorities for the week, and creates a weekly planning file that /wrap-week will fill in with the retrospective. Trigger when the user says "start my week", "plan my week", "weekly planning", or invokes /start-week. Must be run from the root of the Obsidian vault.
argument-hint: "[--weekly-recaps-path <path>]"
---

# Start Week

You are helping the user open the week with intention. Review what's on deck across projects and commitments, help them focus on 2–3 meaningful priorities (not a laundry list), and create the weekly planning file that `/wrap-week` will fill in on Friday.

## Vault Paths (relative to vault root)

- Projects: `01-Projects/` — each project has its own subfolder, typically containing a `PLAN.md`
- Weekly recaps: `02-AreasOfResponsibility/Weekly Recaps/` (override with `--weekly-recaps-path`)
- Daily notes: `02-AreasOfResponsibility/Daily Notes/`

---

## Phase 0: Date Setup

Run via Bash:
```bash
TODAY=$(date +%Y-%m-%d)
DOW=$(date +%u)
WEEK_START=$(date -v-$((DOW - 1))d +%Y-%m-%d 2>/dev/null || date -d "$(date +%Y-%m-%d) -$(($(date +%u)-1)) days" +%Y-%m-%d)
WEEK_END=$(date -v+$((5 - DOW))d +%Y-%m-%d 2>/dev/null || date -d "$(date +%Y-%m-%d) +$((5 - $(date +%u))) days" +%Y-%m-%d)
WEEK_NUM=$(date +%Y-W%V)
WEEK_LABEL=$(date -v-$((DOW - 1))d "+%B %-d" 2>/dev/null || date -d "$(date +%Y-%m-%d) -$(($(date +%u)-1)) days" "+%B %-d")
echo "TODAY=$TODAY WEEK_START=$WEEK_START WEEK_END=$WEEK_END WEEK_NUM=$WEEK_NUM WEEK_LABEL=$WEEK_LABEL"
```

Store TODAY, WEEK_START, WEEK_END, WEEK_NUM (e.g., `2026-W14`), and WEEK_LABEL (e.g., `March 30`).

---

## Phase 1: Gather Context

Run in parallel:

**Projects:** Invoke the `project-index` skill to get the current project listing. This runs a hook script that extracts frontmatter from all `01-Projects/*/PLAN.md` files and returns a formatted index with names, descriptions, areas, and due dates. Use this index for the Phase 2 landscape summary — it is intentionally lightweight. Only do full PLAN.md reads for projects flagged as due within 14 days or ones the user specifically asks about.

**Overdue and high-priority tasks:** Call `get_tasks` on the Todoist MCP server filtered to overdue tasks, plus p1 tasks with any due date this week. These represent carry-in work that needs attention.

**This week's calendar:** Call `list-events` on the Google Calendar MCP server for WEEK_START through WEEK_END. Note: heavy meeting days, key 1:1s or reviews that need prep, any deadlines embedded in event names.

**Last week's recap (for continuity):** Compute the previous week's file path and attempt to read it:
```
02-AreasOfResponsibility/Weekly Recaps/<prev-WEEK_NUM>.md
```
If it exists, extract "## Intentions for Next Week" and "## Carried Forward" sections to surface unfinished business.

**Existing weekly file:** Check if `02-AreasOfResponsibility/Weekly Recaps/WEEK_NUM.md` already exists. If it does, read it — this means start-week has already been run this week. Note this to the user and offer to update priorities rather than start fresh.

If any MCP server is unavailable, note it and continue with the data that is available.

---

## Phase 2: Surface the Landscape

Before asking the user to set priorities, present a concise snapshot of what's on deck. Keep this scannable — it's context, not a briefing:

---

**Week of [WEEK_LABEL]**

**Coming in from last week**
[Items from last week's "Intentions for Next Week" and "Carried Forward" — 2–4 bullets max]
[If no last week recap exists, pull from overdue Todoist tasks instead]

**Projects with momentum or deadlines**
For each active project in `01-Projects/`, one line:
- **[Project Name]** — [1-sentence status] [· Due: DATE if applicable]

Flag any project with a deadline in the next 14 days with ⚠️.

**This week's calendar load**
[Total meetings, any notably heavy days, key events needing prep]

**Overdue / carried tasks** ([N] items)
[List them briefly — enough context to factor into priority-setting]

---

## Phase 3: Set Weekly Priorities

Ask the user directly:

> "Given everything above — what are the **2–3 things** that would make this a successful week? These should be outcomes, not task lists."

Wait for their response. If they list more than 3, gently push back:

> "That's [N] things — which 3 matter most if the week gets compressed?"

Once they've settled on 2–3 priorities, confirm them back:

> "Got it. This week's priorities:
> 1. [Priority 1]
> 2. [Priority 2]
> 3. [Priority 3]"

Then ask: "Anything specific you want to note about approach or constraints for any of these?" Capture their answer as notes under each priority.

---

## Phase 4: Create the Weekly Planning File

Check if `02-AreasOfResponsibility/Weekly Recaps/WEEK_NUM.md` already exists:

- **If it exists:** Use the Edit tool to update the `## Priorities This Week` and `## Key Projects This Week` sections with the output of Phases 2–3. Preserve all other content.
- **If it does not exist:** Use the Write tool to create it with the template below.

```markdown
---
date-range: WEEK_START to WEEK_END
week: WEEK_NUM
tags: [weekly-recap, weekly-plan]
---

# Week of [WEEK_LABEL]

## Priorities This Week

1. [Priority 1]
   [Notes from user, if any]
2. [Priority 2]
   [Notes from user, if any]
3. [Priority 3 — omit if only 2 were set]
   [Notes from user, if any]

## Key Projects This Week

[One line per active project from Phase 2 — name, status, deadline if any]

---
<!-- The sections below are filled in by /wrap-week at the end of the week -->

## The Week in Review

## By the Numbers

## Highlights

## Carried Forward

## Next Week

## Intentions for Next Week

## Areas Reviewed
```

Tell the user: "Created `02-AreasOfResponsibility/Weekly Recaps/WEEK_NUM.md` — `/wrap-week` will fill in the retrospective on Friday."

---

## Quality Notes

- The goal of Phase 3 is focus, not completeness. 2–3 real priorities beat a 10-item list.
- Projects with approaching deadlines should get real weight in priority-setting — don't let them drop.
- If last week's intentions carry directly into this week unchanged, flag that gently: "These look the same as last week — is that intentional, or did something block them?"
- Keep Phase 2 brief. It's context to inform the conversation, not a report to be read in full.
- The weekly file is the source of truth that `/start-day` will read all week — make the priorities crisp and actionable.
