---
name: wrap-week
description: Weekly wrap-up and forward-planning session. Spends 1/3 on this week's retrospective and 2/3 planning next week with clear priorities. Silently runs /project-monitor and /aor-review to inform priority-setting. Finishes by writing the current week's recap and creating next week's planning file. Run on Friday afternoon or Sunday evening. Trigger when the user says "wrap up my week", "weekly recap", "weekly review", or invokes /wrap-week. Must be run from the root of the Obsidian vault.
---

# Wrap Week

You are helping the user close out this week and set up next week for success. The session is intentionally weighted: 1/3 on what happened this week, 2/3 on making sure next week starts with focus and clarity. The output is two files: a completed recap for this week and a pre-populated planning file for next week.

## Arguments

- `--daily-notes-path <path>` — override daily notes folder (default: `02-AreasOfResponsibility/Daily Notes`)
- `--weekly-recaps-path <path>` — override weekly recaps folder (default: `02-AreasOfResponsibility/Weekly Recaps`)
- `--areas-path <path>` — override areas of responsibility root folder (default: `02-AreasOfResponsibility`)
- `--focus <text>` — user-specified focus area or theme for next week (e.g., `--focus "Q2 planning"`)

## Configuration

If a `CLAUDE.md` exists at the vault root with a **Chief of Staff** config block, path values there are used as defaults — no arguments needed. The precedence for each path is:

1. Per-invocation argument (highest)
2. Value from `CLAUDE.md` Chief of Staff block
3. Hardcoded default

Example `CLAUDE.md` block:

```
## Chief of Staff
- daily-notes-path: Journal/Daily
- weekly-recaps-path: Reviews/Weekly
- areas-path: Areas
```

## Vault Paths (relative to vault root)

- Daily notes: `02-AreasOfResponsibility/Daily Notes/`
- Weekly recaps: `02-AreasOfResponsibility/Weekly Recaps/`
- Areas of responsibility: `02-AreasOfResponsibility/` (subfolders, excluding `Daily Notes`, `Weekly Recaps`, `Notes`)

---

## Phase 0: Date Setup

**First, resolve vault paths.** Check `CLAUDE.md` at vault root for a "Chief of Staff" section and read `daily-notes-path`, `weekly-recaps-path`, and `areas-path` values if present. Per-invocation arguments override CLAUDE.md values; CLAUDE.md values override hardcoded defaults. Use the resolved paths everywhere below.

```bash
TODAY=$(date +%Y-%m-%d)
DOW=$(date +%u)
WEEK_START=$(date -v-$((DOW - 1))d +%Y-%m-%d 2>/dev/null || date -d "$(date +%Y-%m-%d) -$(($(date +%u)-1)) days" +%Y-%m-%d)
WEEK_NUM=$(date +%Y-W%V)
# Next week values
NEXT_WEEK_START=$(date -v+$((8 - DOW))d +%Y-%m-%d 2>/dev/null || date -d "$(date +%Y-%m-%d) +$((8 - $(date +%u))) days" +%Y-%m-%d)
NEXT_WEEK_END=$(date -v+$((12 - DOW))d +%Y-%m-%d 2>/dev/null || date -d "$(date +%Y-%m-%d) +$((12 - $(date +%u))) days" +%Y-%m-%d)
NEXT_WEEK_NUM=$(date -v+7d +%Y-W%V 2>/dev/null || date -d "$(date +%Y-%m-%d) +7 days" +%Y-W%V)
echo "TODAY=$TODAY WEEK_START=$WEEK_START WEEK_NUM=$WEEK_NUM NEXT_WEEK_START=$NEXT_WEEK_START NEXT_WEEK_END=$NEXT_WEEK_END NEXT_WEEK_NUM=$NEXT_WEEK_NUM"
```

Store all variables. WEEK_NUM and NEXT_WEEK_NUM follow ISO format (e.g., `2026-W13`, `2026-W14`).

---

## Phase 1: Gather the Week's Data

Run all of the following in parallel:

**Completed tasks:** `find-completed-tasks` from WEEK_START to TODAY. Group by project. Note total count.

**Incomplete/overdue tasks:** `find-tasks` filtered to overdue. These are planned items that didn't happen.

**This week's calendar:** `list-events` for WEEK_START through TODAY. Group by day. Note total meeting hours and any recurring commitments.

Events with titles starting with `[IT]` are intentional focus blocks, not meetings. When counting meetings or summarizing calendar load, exclude `[IT]` events from the meeting count but include them in a separate "Focus time scheduled" tally.

**Next week's calendar:** `list-events` for NEXT_WEEK_START through NEXT_WEEK_END. Note meeting load, any heavy days, and commitments that need prep.

**Daily notes:** Read each `02-AreasOfResponsibility/Daily Notes/YYYY-MM-DD.md` for Mon–Fri this week. For each note that exists, extract: accomplishments, blockers, recurring themes, any project mentions, and end-of-day reflections. Pay special attention to the `### Reflection` subsection within `## End of Day` — these are the user's verbatim thoughts on each day and are the primary source for Phase 2's reflection synthesis. Note how many days have notes vs. don't.

**Current week file:** Check if `02-AreasOfResponsibility/Weekly Recaps/WEEK_NUM.md` exists. If so, read it — preserve existing frontmatter and Priorities/Key Projects sections.

---

## Phase 2: Weekly Recap (condensed — ~1/3 of the session)

Write a tight narrative recap — 150–250 words. This is a synthesis, not a data dump. Write it as if explaining the week to a colleague in two minutes.

Structure:

**The Week in Brief**
One sentence on the dominant theme (e.g., "A heads-down execution week on [project]", "Heavy meeting load with fragmented focus", "Recovery week after last week's crunch").

**Key Accomplishments**
3 most meaningful completions — chosen for impact, not volume. One line each.

**What Didn't Happen**
1–2 honest sentences. Frame constructively: "X was displaced by Y." Flag anything deferred multiple weeks running.

**Week Patterns** (only if the data supports a clear observation)
Examples: "Most productive stretch was Tue–Wed before the afternoon standup block", "Three p1 tasks deferred again."

Present the recap to the user. They can confirm it as-is or add a note. Keep this phase brief — the goal is to capture the week, not relitigate it.

### Daily Reflection Themes

After the narrative recap, synthesize the `### Reflection` entries from this week's daily notes. Look for:

- **Recurring topics** — themes or concerns that appeared more than once (e.g., a relationship friction, a recurring blocker, an energy pattern)
- **1:1 fodder** — things worth raising with a direct report, manager, or peer in an upcoming 1:1
- **Project or idea seeds** — nascent ideas or problems the user surfaced that haven't turned into a Todoist task yet
- **Signals worth watching** — anything that felt like a one-off but might be worth monitoring

Present this as a short bulleted list (3–6 items max). Label each with one of: `[1:1]`, `[idea]`, `[pattern]`, or `[watch]`. Skip the section entirely if fewer than 2 daily notes had reflections.

Example:
```
**From this week's reflections:**
- [pattern] Three days mentioned feeling context-switched before 10am — calendar structure may be a factor
- [1:1] Tension with the API naming decision came up Tue + Thu — worth surfacing with the team
- [idea] Mentioned wanting a "one-pager for onboarding" twice — no task exists yet
```

### Weekly Reflection

After presenting the recap and reflection themes, invite the user into a short reflection conversation. Ask the questions below — not all at once as a list, but conversationally, one or two at a time. Read the room: if the user is giving rich answers, keep going; if they're brief, don't force it.

**Prompt areas to cover (pick the most relevant 3–4 based on what's come up this week):**

- **Energy & mood** — "How are you feeling coming out of this week — energized, drained, somewhere in between?"
- **What went well / what didn't** — "What worked this week? Anything that felt like it didn't go the way you wanted?"
- **What's exciting** — "Anything you're genuinely looking forward to or feeling good about right now?"
- **What's bothering you** — "Anything sitting with you that you haven't fully resolved — a decision, a relationship, a nagging problem?"
- **Ideas brewing** — "Any ideas you've been turning over in the back of your mind — projects, experiments, things you want to try?"
- **What you need** — "Is there anything you need more or less of right now — focus time, clarity, support, rest?"

Listen for items that sound like **latent priorities or projects** — things that don't have a Todoist task yet but probably should. Flag these explicitly:

> "That sounds like it might be worth capturing as a project or priority — want me to note it for Phase 4, or add it to your inbox now?"

Record the full exchange in the recap file under `## Weekly Reflection`. Write it as a brief structured summary (not a transcript), capturing the user's answers against each area covered. Use "—" for any area not discussed.

---

## Phase 3: Silent Context Gathering

Before priority-setting, gather structured context without prompting the user. Run in parallel:

- **`/project-manager:project-monitor --summary`** — returns a structured list of active projects with status, deadline, and flag notes
- **`/aor-review --summary`** — returns a structured list of AORs with open task counts, oldest task age, and health flags
- **Cross-week pattern read** — glob for the 4 most recent weekly recap files in the weekly recaps folder (sorted by filename descending, skip the current week's file). For each prior week file that exists, extract: `## Priorities This Week`, `## Intentions for Next Week`, `## Carried Forward`, and any `[pattern]`-labeled items from `## Daily Reflection Themes`. 

Store all results internally for use in Phase 4. Do not display them to the user yet.

**Cross-week signals to identify from the prior week files:**

- **Recurring carried priorities** — any priority that appears in 2+ consecutive weeks' "Intentions for Next Week" or "Carried Forward" sections without being completed. Flag: "This has been on the list for N weeks."
- **Neglected AORs** — any AOR appearing unflagged in recent weeks that now shows up in the aor-review summary. Or any AOR that never appears as a priority over 3+ weeks.
- **Calendar saturation trend** — if "By the Numbers" meeting hours are available in prior weeks, note whether meeting load has been increasing.
- **Recurring daily note patterns** — any `[pattern]` or `[watch]` theme that appeared across multiple weeks without a project or task addressing it.

Store these cross-week signals as a separate list for Phase 4.

---

## Phase 4: Priority Synthesis (the core of the session)

Now present the full landscape and work with the user to set 2–3 priorities for next week.

### 4a: Surface the Inputs

Present a structured summary of everything gathered:

```
## What I'm seeing for next week

**From this week's daily notes:**
[2–3 themes, blockers, or unresolved items pulled from the notes]

**Active projects:**
[List each project with its status from Phase 3a — flag stalled/needs-attention/deadline]

**Areas of responsibility:**
[List flagged areas from Phase 3b with brief reason]

**Next week's calendar:**
[Total meeting count and hours, any heavy days, key commitments needing prep]

**Carried forward from this week:**
[Top 3 overdue/unfinished items]

**Cross-week patterns** (only if signals exist from Phase 3):
[Surface each signal with context — e.g., "Strategy doc has appeared in 'Intentions for Next Week' for 4 consecutive weeks without completion — either it needs a project plan or it should be deprioritized." or "AOR [X] has had no priority assigned in 3 weeks — is this intentional?" or "Calendar load has trended up 3 weeks in a row — proactive time may be getting crowded out."]
```

If the user passed `--focus`, surface it here: "You mentioned wanting to focus on [focus] — I'll factor that in."

If cross-week patterns are present, name them explicitly before asking about next week's priorities — they're often the most useful signal because they're invisible from inside a single week. Don't bury them.

Then explicitly ask: "Is there anything specific you want to make sure gets done next week, or a theme you want to emphasize?"

### 4b: Propose Priority Candidates

Based on all inputs, propose 4–6 candidate priorities with rationale:

```
**Candidate priorities for next week:**

1. [Priority name] — [why: e.g., "Project X has 3 open tasks and a deadline in 10 days"]
2. [Priority name] — [why: e.g., "Stalled since last week — needs a push to move forward"]
3. [Priority name] — [why: e.g., "AOR [area] has 7 open tasks, oldest is 45 days — time to clear or project-ize"]
4. [Priority name] — [why: e.g., "You mentioned this in your Tuesday daily note as a blocker"]
5. [Priority name] — [why: e.g., "Monday has 3 meetings around this topic — good week to make a decision"]
```

Ask: "Which 2–3 of these do you want as your priorities for next week? You can pick from the list, adjust them, or give me something different."

### 4c: Priority Deep-Dive

For each confirmed priority (one at a time):

1. **Define done:** "What does success look like for this by end of next week?" (brief — one sentence)
2. **Task check:** Surface any existing Todoist tasks that support this priority. If none exist, note the gap and offer to create a task inline.
3. **Blockers:** "Anything that needs to happen first, or anyone you need to loop in?"

Keep each deep-dive tight — the goal is clarity, not exhaustive planning.

### 4d: Next Week Framing

After priorities are set, briefly review:

- **Calendar load:** Flag any days with >4 hours of back-to-back meetings
- **Key meetings to prep for:** Any next-week calendar events needing prep based on the project/AOR context
- **Known constraints:** Travel, blocked time, dependencies

Check if `/start-week` has already been run for next week (i.e., does `NEXT_WEEK_NUM.md` already have `[IT]` blocks?). If not, remind the user that `/start-week` can schedule focus blocks for next week.

Ask: "Any intention or theme you want to carry into next week?" Capture their answer for the planning file.

---

## Phase 5: Create Missing Todoist Tasks

For any priority deep-dive that surfaced a task gap, offer to create the tasks now:

"For [Priority], you don't have any open Todoist tasks. Want me to create: [suggested task(s)]?"

Batch all `add-task` calls together after confirming with the user.

---

## Phase 6: Write Output Files

### File 1 — Current Week Recap

Path: `02-AreasOfResponsibility/Weekly Recaps/WEEK_NUM.md`

**If the file already exists** (from `/start-week`):
- Read it, preserve frontmatter + `## Priorities This Week` + `## Key Projects This Week` exactly
- Fill in or replace the retrospective sections (The Week in Review, By the Numbers, Highlights, Carried Forward, Next Week, Intentions for Next Week, Areas Reviewed)

**If the file does not exist**, create it with the full template.

```markdown
---
date-range: WEEK_START to TODAY
week: WEEK_NUM
tags: [weekly-recap, weekly-plan]
---

# Week of [Month Day] — [Month Day, Year]

## The Week in Review

[Narrative from Phase 2 — 150–250 words]

## By the Numbers

- Tasks completed: X
- Tasks carried forward: Y
- Meetings: Z ([N] hours)
- Daily notes written: N/5

## Highlights

- [Top accomplishment 1]
- [Top accomplishment 2]
- [Top accomplishment 3]

## Carried Forward

[Incomplete items and where they're headed]

## Daily Reflection Themes

[Synthesized themes from this week's daily note reflections — labeled [1:1], [idea], [pattern], or [watch]. Omit section if fewer than 2 daily notes had reflections.]

## Weekly Reflection

[Structured summary of the reflection conversation — areas covered: energy/mood, what went well/didn't, excitement, concerns, ideas, needs. Use "—" for areas not discussed. Latent priorities or project seeds flagged here.]

## Areas Reviewed

| Area        | Open Tasks | Oldest Task | Health  | Note                                  |
| ----------- | ---------- | ----------- | ------- | ------------------------------------- |
| [Area Name] | X          | Y days      | ok/flag | [action taken or observation]         |
```

### File 2 — Next Week Planning File

Path: `02-AreasOfResponsibility/Weekly Recaps/NEXT_WEEK_NUM.md`

Check if this file already exists. If it does, skip creating it (don't overwrite manual edits).

If it does not exist, create it pre-populated with the priorities and project context from this session:

```markdown
---
date-range: NEXT_WEEK_START to NEXT_WEEK_END
week: NEXT_WEEK_NUM
tags: [weekly-recap, weekly-plan]
---

# Week of [Next Week Month Day] — [Next Week Month Day, Year]

## Priorities This Week

1. [Priority 1 from Phase 4c]
   [Success definition from deep-dive]
2. [Priority 2 from Phase 4c]
   [Success definition from deep-dive]
3. [Priority 3 from Phase 4c — omit if only 2 were set]
   [Success definition from deep-dive]

## Key Projects This Week

[One line per active project with status from project-monitor summary — name · status · deadline if any]

---
<!-- The sections below are filled in by /wrap-week at the end of next week -->

## The Week in Review
## By the Numbers
## Highlights
## Carried Forward
## Areas Reviewed
```

---

## Closing

Tell the user:

```
Week [WEEK_NUM] wrapped. Next week's planning file is ready at Weekly Recaps/[NEXT_WEEK_NUM].md.

You're starting [next Monday's date] with [N] priorities:
1. [Priority 1]
2. [Priority 2]
[3. Priority 3 if set]

Run /start-week on Monday to pull your briefing, or your planning file is already there if you want to jump straight in.
```

---

## Decision Tracking

As you work through this session, watch for decision signals from the user — statements like "I don't need that", "we already have a task for this", "we decided to go with X", "that's not relevant to me anymore", "skip that". When you encounter one:

- **Scope:** Is this tied to a specific project being discussed? → write to `01-Projects/<project>/decisions.yaml`. Otherwise → write to `decisions.yaml` at vault root.
  - Email and task dispositions are always global.
  - Approach and architecture decisions are project-scoped if a project is clearly in context; otherwise global.
- **Write immediately** — don't wait until the end of the session. Use file write or a Bash heredoc append.
- **Don't call it out** unless you're uncertain about scope or TTL — just capture it silently.
- **Entry format:** generate ID as `dec_YYYYMMDD_<4 hex chars>`, set `created` to today, set `expires` using the TTL tier that fits:
  - `email` / `task` → +7 days
  - `approach` / `process` → +21 days
  - `strategic` → +90 days

```yaml
- id: dec_20260422_a1b2
  text: "We're going with GraphQL federation — decided in wrap-week 2026-W16"
  category: approach
  created: 2026-04-22
  expires: 2026-05-13
```

If the file doesn't exist yet, create it. Preserve all existing entries.

**Expiring-soon review (end of session):** Before closing, check `decisions.yaml` for any entries expiring within the next 7 days. If any exist, surface them briefly: "These decisions expire soon — worth extending?" List each with its text and expiry date. If the user says yes (for any), update the `expires` field in the file by adding 21 days from today.

## Quality Notes

- Keep Phase 2 tight — resist the urge to expand the retrospective. The value is in the forward planning.
- Priority deep-dives should feel like a brief alignment conversation, not a planning marathon. One sentence of "done" is enough.
- The next-week file should feel ready to use on Monday, not like a rough draft.
- Don't surface every project and area in the priority candidates — curate to the most actionable 4–6. The user can volunteer others.
- Cross-week patterns are often more valuable than single-week observations. If the same thing has been deferred 3+ weeks, say so explicitly — don't soften it.
- If prior weekly recap files don't exist yet (first few weeks of usage), skip the cross-week section gracefully and note that patterns will emerge over time.
- If a week had sparse data (few daily notes, light task history), be honest about that and lean on calendar + project state instead.
