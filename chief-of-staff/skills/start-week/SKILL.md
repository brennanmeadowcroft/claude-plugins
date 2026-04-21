---
name: start-week
description: Weekly planning session — reviews projects for due dates and open work, guides the user to set 2–3 priorities for the week, and creates a weekly planning file that /wrap-week will fill in with the retrospective. Trigger when the user says "start my week", "plan my week", "weekly planning", or invokes /start-week. Must be run from the root of the Obsidian vault.
---

# Start Week

You are helping the user open the week with intention. Review what's on deck across projects and commitments, help them focus on 2–3 meaningful priorities (not a laundry list), and create the weekly planning file that `/wrap-week` will fill in on Friday.

## Arguments

- `--weekly-recaps-path <path>` — override weekly recaps folder (default: `02-AreasOfResponsibility/Weekly Recaps`)

## Configuration

If a `CLAUDE.md` exists at the vault root with a **Chief of Staff** config block, the `weekly-recaps-path` value there is used as the default — no argument needed. The precedence is:

1. `--weekly-recaps-path` argument (highest)
2. `weekly-recaps-path` in `CLAUDE.md` Chief of Staff block
3. Hardcoded default: `02-AreasOfResponsibility/Weekly Recaps`

Example `CLAUDE.md` block:

```
## Chief of Staff
- weekly-recaps-path: Reviews/Weekly
```

## Vault Paths (relative to vault root)

- Projects: `01-Projects/` — each project has its own subfolder, typically containing a `PLAN.md`
- Weekly recaps: resolved `weekly-recaps-path` (default: `02-AreasOfResponsibility/Weekly Recaps/`)
- Daily notes: `02-AreasOfResponsibility/Daily Notes/`

---

## Phase 0: Date Setup

**First, resolve the weekly recaps path.** Check `CLAUDE.md` at vault root for a "Chief of Staff" section and read the `weekly-recaps-path` value if present. If `--weekly-recaps-path` was passed, it overrides the CLAUDE.md value. If neither is set, use `02-AreasOfResponsibility/Weekly Recaps`. Use the resolved path everywhere below.

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

**Projects:** Invoke the `project-manager:project-index` skill to get the current project listing. This runs a hook script that extracts frontmatter from all `01-Projects/*/PLAN.md` files and returns a formatted index with names, descriptions, areas, and due dates. Use this index for the Phase 2 landscape summary — it is intentionally lightweight. Only do full PLAN.md reads for projects flagged as due within 14 days or ones the user specifically asks about.

**Overdue and high-priority tasks:** Call `find-tasks` filtered to overdue tasks, plus p1 tasks with any due date this week. These represent carry-in work that needs attention.

**This week's calendar:** Call `list-events` on the Google Calendar MCP server for WEEK_START through WEEK_END. Note: heavy meeting days, key 1:1s or reviews that need prep, any deadlines embedded in event names.

**Last week's recap (for continuity):** Compute the previous week's file path and attempt to read it:
```
02-AreasOfResponsibility/Weekly Recaps/<prev-WEEK_NUM>.md
```
If it exists, extract "## Intentions for Next Week" and "## Carried Forward" sections to surface unfinished business.

**AOR health (silent):** Invoke `/aor-review --summary` to get area-of-responsibility health flags without an interactive session. This surfaces AORs with stale tasks, high task counts, or patterns that suggest a project should spin up. Store the output for use in Phase 2 priority synthesis.

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

Before asking the user, synthesize 2–3 candidate priorities from the data gathered in Phases 1–2. Come with a recommendation, not a blank page.

**Candidate priority signals to weigh:**
- Projects with deadlines in the next 14 days (⚠️ flagged) — deadline pressure is a strong signal
- Intentions from last week that didn't get done — carried work needs a deliberate decision
- AOR health flags from `/aor-review --summary` — stale areas or clustering patterns that need attention
- Overdue p1 tasks — these represent commitments already slipping

**Present candidates with reasoning:**

> "Based on what I'm seeing, here are my candidates for this week's top priorities:
>
> 1. **[Candidate 1]** — [1-sentence reasoning, e.g., 'deadline in 8 days, no tasks moved last week']
> 2. **[Candidate 2]** — [1-sentence reasoning]
> 3. **[Candidate 3]** — [1-sentence reasoning, or 'AOR flagged for 2 weeks, overdue for attention']
>
> What would you change? Anything to add, swap out, or reorder?"

Wait for their response. Treat this as a refinement conversation, not a confirmation. If they reject a candidate, ask what should replace it. If they accept with modifications, incorporate them. If they list more than 3, gently push back:

> "That's [N] things — which 3 matter most if the week gets compressed?"

Once settled on 2–3 priorities, confirm them back:

> "Got it. This week's priorities:
> 1. [Priority 1]
> 2. [Priority 2]
> 3. [Priority 3]"

**Meeting intelligence:** Now that the priorities are confirmed, invoke the `exec-assistant:ask-meetings` skill once per priority, querying for objections, concerns, or blockers raised in recent meetings. Use each priority's project tag (if known from the project index) to filter results — e.g., query: `"blockers or concerns about [Project Name]"` with `tag:[project-tag]`. Silently synthesize the results; only surface findings that are actionable (a specific concern raised, a dependency flagged, someone waiting on something). Fold any findings into the blocker prompt below rather than presenting them as a separate report.

Then for each priority, ask a brief follow-up in one prompt:

> "For each priority, anything to note on:
> - Approach or constraints?
> - Blockers that could stop progress? [If ask-meetings surfaced something specific, name it here: e.g., "In last week's review, [concern] was raised — is that still live?"]
> - The immediate next task to move it forward?"

Capture their answers as structured notes under each priority in the weekly file (constraints, blockers, next task). If they don't have an answer for a field, omit it — don't force completeness.

**Time audit:** Before moving on, calculate available focused hours. Count total calendar hours this week (from Phase 1 data), subtract committed meeting time, and surface the result:

> "You have roughly [N] hours available outside of meetings this week. With [M] priorities, that's about [N/M] hours per priority — does that feel realistic?"

If the math is tight (less than 4 hours per priority), prompt: "The calendar is pretty full — do you want to adjust the priorities list, or are some of these shorter efforts?"

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

[One line per project directly supporting the 2–3 priorities above — name, status, deadline if any. Do NOT list all active projects; only include projects tied to a selected priority.]

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

## Phase 5: Suggest Focus Time Blocks

Before closing the session, propose dedicated focus blocks that align with the user's top priorities.

1. **Identify calendar gaps:** Look at this week's calendar (already fetched in Phase 1) and identify gaps of 60+ minutes where no meetings are scheduled. These are candidate focus windows.

2. **Gather priority context:** Review the confirmed weekly priorities from Phase 3 and surface any relevant Todoist tasks that support them. If the `find-tasks` results from Phase 1 lack sufficient detail, call `find-tasks` again with a filter for tasks due this week.

3. **Propose 2–4 focus blocks:** Map suggestions to the user's top priorities. Each suggestion should include:
   - Day and time window (e.g., "Tuesday 9:00–11:00")
   - The priority/project it supports
   - A proposed calendar event title in the format: `[IT] {Project Name}` (e.g., `[IT] Platform Migration`)

4. **Read preferences:** Before suggesting blocks, check if `~/.claude-personal/context/preferences-and-constraints.md` exists. If it does, read the `## Calendar Conventions` section to understand the user's preferences for managing calendar time (e.g., preferred deep-work hours, times to avoid). Use this to make suggestions more relevant.

5. **Present suggestions:** Offer the user a choice:
   > "Based on your priorities and calendar gaps, here are some suggested focus blocks:
   > - Tuesday 9:00–11:00 → `[IT] Platform Migration`
   > - Wednesday 2:00–4:00 → `[IT] Hiring Pipeline`
   > Want me to block any of these? They'll be marked as Free so they don't block meeting scheduling."

6. **Create approved blocks:** For any blocks the user approves, create them on Google Calendar using the Google Calendar MCP (`create-event`). Set them as:
   - Title: `[IT] {Project Name}`
   - Status: Free (so they show as available for scheduling)
   - No attendees

7. **Confirm completion:** After creating the blocks, tell the user which ones were created.

---

## Quality Notes

- **The goal is strategic focus and completion, not coverage.** 2–3 real priorities that get finished beat shallow progress across 7 things. When the user tries to add more, push back: "Which 3 give you the most meaningful outcomes if the week goes sideways?"
- **Key Projects This Week ≠ all active projects.** Only list projects directly tied to the selected priorities. The section exists to show supporting context for the focus, not to be a project inventory.
- Come to the priority conversation with a recommendation. The user's job is judgment; the skill's job is synthesis. Don't ask a blank-page question when the data already suggests an answer.
- Projects with approaching deadlines should get real weight in priority-setting — don't let them drop.
- If last week's intentions carry directly into this week unchanged, flag that gently: "These look the same as last week — is that intentional, or did something block them?"
- Keep Phase 2 brief. It's context to inform the conversation, not a report to be read in full.
- The time audit is not a blocker — it's a mirror. If the math is tight, surface it and let the user decide. Don't adjust priorities without asking. If the math shows the priorities can't all fit, suggest rescheduling lower-urgency ones rather than padding the list.
- Capturing blockers and next tasks for each priority is critical — a priority with no clear next action won't move.
- The weekly file is the source of truth that `/start-day` will read all week — make the priorities crisp and actionable.
