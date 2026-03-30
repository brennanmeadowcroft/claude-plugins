---
name: wrap-week
description: Weekly retrospective — pulls completed Todoist tasks, Google Calendar events, and Obsidian daily notes from Monday through today, synthesizes a narrative weekly recap, saves it to Obsidian, and previews next week. Run on Friday afternoon or Sunday evening. Trigger when the user says "wrap up my week", "weekly recap", "weekly review", or invokes /wrap-week.
argument-hint: "[--daily-notes-path <path>] [--weekly-recaps-path <path>]"
---

# Wrap Week

You are helping the user write a meaningful weekly retrospective. This is a narrative synthesis, not a list dump. The goal is to tell the story of the week in a way that helps the user see patterns, celebrate progress, and prepare thoughtfully for next week.

Default paths (override with arguments):
- Daily notes: `Daily Notes/`
- Weekly recaps: `Weekly Recaps/`

## Phase 0: Pre-Flight Check and Date Setup

1. Get today's date and compute the week range via Bash:
```bash
# Get today
TODAY=$(date +%Y-%m-%d)
# Get Monday of current week (macOS)
WEEK_START=$(date -v-$(date +%u)d +%Y-%m-%d 2>/dev/null || date -d "last monday" +%Y-%m-%d)
# ISO week number
WEEK_NUM=$(date +%Y-W%V)
echo "TODAY=$TODAY WEEK_START=$WEEK_START WEEK_NUM=$WEEK_NUM"
```

Store WEEK_START (Monday), TODAY (end of week), and WEEK_NUM (e.g., `2026-W13`).

2. Verify all three MCP servers are reachable. If any fails, STOP and provide the fix command.
3. Get timezone via `get-current-time` on the google-calendar server.

## Phase 1: Gather the Week's Data

Run in parallel where possible:

**Completed tasks:** Call `get_completed_tasks` filtered from WEEK_START to TODAY. Group by project. Note the total count.

**Incomplete/carried tasks:** Call `get_tasks` filtered to overdue. These are things that were planned but didn't happen this week.

**Calendar events:** Call `list-events` for WEEK_START through TODAY. Group by day. Note total meeting hours.

**Daily notes:** For each day Monday through today, attempt `read_note` on `<daily-notes-path>/YYYY-MM-DD.md`. Collect each note that exists. Note how many days have a daily note vs. how many don't.

If daily notes are sparse or missing, acknowledge that and work with what's available from Todoist and Calendar.

## Phase 2: Synthesize the Weekly Narrative

Write a narrative recap — not a data dump. Aim for 300–500 words that tell the story of the week. Synthesize across all sources rather than summarizing each one separately.

Structure the narrative around these themes (use judgment about which are relevant this week):

**The Big Picture**
What was the dominant theme? Examples: "This was primarily a deep-work week on [project]", "This week was fragmented across multiple initiatives with heavy meeting load", "A recovery week after last week's crunch."

**Key Accomplishments**
3–5 most significant completions, chosen for impact not volume. Not just the most tasks — the most meaningful ones.

**Meetings and Decisions**
What did the calendar reveal? Any significant conversations, decisions made, or relationships advanced?

**What Didn't Happen**
Honest acknowledgment of things that were planned but didn't happen. Frame constructively: "X was planned but got displaced by Y." Flag anything that has been deferred multiple weeks in a row.

**Patterns and Observations** (include if the data supports it)
Examples: "Most productive days were Tuesday/Thursday when you had clear morning blocks", "Three p1 tasks were deferred again — worth a priority audit", "Meeting load was above average at X hours."

**Tone from Daily Notes** (include only if daily notes exist)
If end-of-day reflections are present in the daily notes, synthesize the emotional arc of the week honestly.

## Phase 3: Next Week Preview

1. Call `list-events` for next Monday through Friday.
2. Call `get_tasks` filtered to next week's due dates, plus any still-overdue tasks being carried forward.

Present:
- **Key commitments** — calendar events next week that may need prep (e.g., presentations, important meetings)
- **Priorities** — top tasks due next week, especially any carried over from this week
- **Suggested focus** — given this week's patterns, what should next week's emphasis be?

Ask: "Is there anything you want to set as an intention for next week?" Incorporate their answer into the weekly note.

## Phase 4: Save Weekly Recap to Obsidian

Construct the note filename: `<weekly-recaps-path>/WEEK_NUM.md` (e.g., `Weekly Recaps/2026-W13.md`)

Use `write_note` to save:

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

[Incomplete items and where they're headed — e.g., "Fix auth bug → rescheduled to [date]"]

## Next Week

[Preview from Phase 3 — calendar commitments and top priorities]

## Intentions for Next Week

[User's stated intention from Phase 3, or "—" if skipped]
```

Tell the user where the file was saved: "Saved to `Weekly Recaps/WEEK_NUM.md`"

## Quality Notes

- The narrative should feel human and thoughtful — write it as if explaining the week to a colleague, not generating a report
- Don't list every completed task — curate and interpret
- If a week had very few completed tasks or sparse data, be honest about that rather than padding the narrative
- The recap should be something the user would find meaningful to re-read months later
- ISO week filenames (`2026-W13.md`) sort naturally in Obsidian and are easy to query for quarterly reviews
