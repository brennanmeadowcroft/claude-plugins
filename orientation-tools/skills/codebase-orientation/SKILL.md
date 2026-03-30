---
name: codebase-orientation
description: Entry point for codebase orientation. Checks dependencies, assesses your familiarity and goals, then routes to the right exploration skill (cartographer, layers, mikado, or health). Use when you want help understanding a new or unfamiliar codebase, or when planning a large feature or refactor.
argument-hint: "[--path <dir>]"
---

# Codebase Orientation — Dispatcher

You are helping the user orient to a codebase. Your job is to check tooling, assess their situation, and route them to the right exploration skill.

## Step 1: Check dependencies

Run `orientation-tools/scripts/check-dependencies.sh` using the Bash tool, passing the target path as an argument if one was provided (or omit for cwd auto-detection).

Display the output to the user only if any tools are missing (i.e., the output contains `[✗]` lines). If all tools for the detected stack are present, proceed silently.

If tools are missing, note: "Some optional tools are not installed — dependency diagram generation and health analysis may be limited. See above for install commands. Continuing with orientation."

## Step 2: Determine the target path

If the user passed `--path <dir>`, use that as the target directory for all analysis. Otherwise, use the current working directory.

## Step 3: Check for prior orientation work

Look for `.orientation/CODEBASE_MAP.md` in the target path. If it exists, the user has already run the cartographer — note this context.

## Step 4: Assess the user's situation and route

Read the user's message for signals across three dimensions simultaneously, then route in a single step.

**Dimension A — Large-scale planning signal:** Does the user's message indicate a *large* or *risky* change — not just any task? Keywords: "refactor", "large feature", "major change", "risky", "fragile", "dangerous", "where should I be careful", "technical debt", "big change", "overhaul", "rewrite". A general task ("add an endpoint", "fix a bug") does NOT qualify — only use this when scope or risk is explicitly the concern.

**Dimension B — Familiarity:**
- **New** — never worked in this codebase
- **Somewhat familiar** — looked around or made a few changes
- **Familiar** — knows the codebase, needs help with a specific area

**Dimension C — Has a specific task:**
- **Yes** — specific goal in mind
- **No** — wants to understand the codebase generally
- **Sort of** — general area but not a specific task

If you can determine all three dimensions from the user's initial message, route immediately. If you cannot, ask the user up to two clarifying questions (use AskUserQuestion) — familiarity and whether they have a task. You do not need to ask about planning intent if it was already clear from their message.

**Routing:**

If the **large-scale planning signal** is present:
- Suggest `/codebase-health` as a recommended first step: "Since you're planning a large change, a health analysis can help identify risky areas before you start. I'd suggest running `/codebase-health` first, then we can orient to the structure."
- Let the user decide whether to run it — don't invoke it automatically.
- After health runs (or if the user declines), continue routing per the table below.

| Familiarity | Has Task? | Recommendation |
|------------|-----------|----------------|
| New | No | `/codebase-cartographer` — Start with the big picture. Produces reference docs you can come back to. |
| New | Yes | `/codebase-cartographer` first, then suggest `/codebase-mikado` for the specific task |
| New | Sort of | `/codebase-cartographer` — Map the territory first, then you'll know where to dig in |
| Somewhat | No | `/codebase-layers` — Interactive guided tour to deepen understanding |
| Somewhat | Yes | `/codebase-mikado` — Trace the dependencies for the specific change |
| Somewhat | Sort of | `/codebase-layers` — Explore interactively, focusing on the area of interest |
| Familiar | No | `/codebase-layers` — Focus on areas known least |
| Familiar | Yes | `/codebase-mikado` — Jump straight to tracing the change |
| Familiar | Sort of | `/codebase-layers` — Explore the specific area of interest |

**If `.orientation/CODEBASE_MAP.md` already exists:**
- Mention that prior orientation docs exist in `.orientation/`
- Bias toward `/codebase-layers` or `/codebase-mikado` since the mapping is done
- Only suggest re-running cartographer if the user thinks the map may be outdated

Tell the user which skill you recommend and why, then invoke it using the Skill tool. Pass through the `--path` argument if one was provided.
