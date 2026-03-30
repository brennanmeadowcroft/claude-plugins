---
name: wrap-week
description: Weekly retrospective — pulls completed Todoist tasks, Google Calendar events, and Obsidian daily notes from Monday through today, synthesizes a narrative weekly recap, saves it to Obsidian, and previews next week. Run on Friday afternoon or Sunday evening. Trigger when the user says "wrap up my week", "weekly recap", "weekly review", or invokes /wrap-week. Must be run from the root of the Obsidian vault.
---

# Wrap Week

You are helping the user write a meaningful weekly retrospective. This is a narrative synthesis, not a list dump. The goal is to tell the story of the week in a way that helps the user see patterns, celebrate progress, and prepare thoughtfully for next week.

## Vault Paths (relative to vault root)

- Daily notes: `02-AreasOfResponsibility/Daily Notes/`
- Weekly recaps: `02-AreasOfResponsibility/Weekly Recaps/`

## Phase 0: Date Setup

Run via Bash:
```bash
TODAY=$(date +%Y-%m-%d)
# Day of week as number (1=Mon, 7=Sun)
DOW=$(date +%u)
# Monday of current week
WEEK_START=$(date -v-$((DOW - 1))d +%Y-%m-%d 2>/dev/null || date -d "$(date +%Y-%m-%d) -$(($(date +%u)-1)) days" +%Y-%m-%d)
# ISO week number
WEEK_NUM=$(date +%Y-W%V)
echo "TODAY=$TODAY WEEK_START=$WEEK_START WEEK_NUM=$WEEK_NUM"
```

Store WEEK_START (Monday), TODAY, and WEEK_NUM (e.g., `2026-W13`).

## Phase 1: Gather the Week's Data

Run in parallel where possible:

**Completed tasks:** Call `get_completed_tasks` on the Todoist MCP server filtered from WEEK_START to TODAY. Group by project. Note the total count.

**Incomplete/carried tasks:** Call `get_tasks` filtered to overdue. These are things that were planned but didn't happen this week.

**Calendar events:** Call `list-events` on the Google Calendar MCP server for WEEK_START through TODAY. Group by day. Note total meeting hours.

**Daily notes:** For each day Monday through today, attempt to read `02-AreasOfResponsibility/Daily Notes/YYYY-MM-DD.md` using the Read tool. Collect each note that exists. Note how many days have a daily note vs. how many don't.

If daily notes are sparse or missing, acknowledge that and work with what's available from Todoist and Calendar.

## Phase 2: Synthesize the Weekly Narrative

Write a narrative recap — not a data dump. Aim for 300–500 words that tell the story of the week. Synthesize across all sources rather than summarizing each one separately.

Structure the narrative around these themes (use judgment about which are relevant this week):

**The Big Picture**
What was the dominant theme? Examples: "This was primarily a deep-work week on [project]", "This week was fragmented across multiple initiatives with a heavy meeting load", "A recovery week after last week's crunch."

**Key Accomplishments**
3–5 most significant completions, chosen for impact not volume. Not just the most tasks — the most meaningful ones.

**Meetings and Decisions**
What did the calendar reveal? Any significant conversations, decisions made, or relationships advanced?

**What Didn't Happen**
Honest acknowledgment of things that were planned but didn't happen. Frame constructively: "X was planned but got displaced by Y." Flag anything deferred multiple weeks in a row.

**Patterns and Observations** (only if the data supports it)
Examples: "Most productive days were Tuesday/Thursday when you had clear morning blocks", "Three p1 tasks were deferred again — worth a priority audit."

**Tone from Daily Notes** (only if daily notes exist with reflections)
If end-of-day reflections are present, synthesize the emotional arc of the week honestly.

## Phase 3: Next Week Preview

1. Call `list-events` for next Monday through Friday.
2. Call `get_tasks` filtered to next week's due dates, plus any still-overdue tasks being carried forward.

Present:
- **Key commitments** — calendar events next week that may need prep
- **Priorities** — top tasks due next week, especially any carried from this week
- **Suggested focus** — given this week's patterns, what should next week's emphasis be?

Ask: "Is there anything you want to set as an intention for next week?" Incorporate their answer into the recap note.

## Phase 4: Save Weekly Recap

Use the Write tool to save `02-AreasOfResponsibility/Weekly Recaps/WEEK_NUM.md`:

```markdown
---
date-range: WEEK_START to TODAY
week: WEEK_NUM
tags: [weekly-recap]
---

# Week of [Month Day] — [Month Day, Year]

## The Week in Review

[Narrative from Phase 2 — 300–500 words]

## By the Numbers

- Tasks completed: X
- Tasks carried forward: Y
- Meetings: Z ([N] hours)
- Daily notes written: N/5

## Highlights

[Bullet list of 3–5 key accomplishments]

## Carried Forward

[Incomplete items and where they're headed]

## Next Week

[Preview from Phase 3 — calendar commitments and top priorities]

## Intentions for Next Week

[User's stated intention, or "—" if skipped]
```

Tell the user: "Saved to `02-AreasOfResponsibility/Weekly Recaps/WEEK_NUM.md`"

## Quality Notes

- The narrative should feel human and thoughtful — write it as if explaining the week to a colleague, not generating a report
- Don't list every completed task — curate and interpret
- If a week had sparse data, be honest about that rather than padding the narrative
- The recap should be something the user would find meaningful to re-read months later
- ISO week filenames (`2026-W13.md`) sort naturally and are easy to query for quarterly reviews
