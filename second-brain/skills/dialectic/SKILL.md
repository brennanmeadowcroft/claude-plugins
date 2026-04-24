---
name: dialectic
description: Socratic thinking partner for working through ideas, hypotheses, and half-formed thoughts. Presses for clarity, surfaces assumptions, and pulls from existing vault notes to support or challenge the idea. Trigger when the user wants to think through an idea, test a hypothesis, explore a concept, or reason about a claim — without necessarily ingesting new content. Also trigger on phrases like "help me think through", "I have an idea", "what do you think about", "let's reason about", or "I want to explore the idea that". Must be run from the root of the Obsidian vault.
---

# Dialectic

Help the user think through an idea rigorously. The goal is not to validate — it's to pressure-test, sharpen, and connect. A good idea survives scrutiny. A great one gets better from it.

There are five phases. Move at the user's pace. The first three phases are where the real thinking happens — don't rush to synthesis.

## Arguments

- `--idea "<text>"` — seed the idea directly; if provided, skip the opening prompt and enter Phase 1 with this as the starting claim

If no argument is provided, open by asking the user: **"What's the idea you want to think through?"**

---

## Phase 1 — Articulation

Goal: Get the idea stated precisely before analyzing it. An idea that can't be stated plainly usually can't be evaluated either.

### Step 1: One-sentence statement

Ask the user: **"State the idea in one sentence as if explaining it to someone who doesn't share your context."**

If they struggle or hedge — that's useful signal. Help them identify whether the difficulty is about complexity (the idea genuinely has many parts) or vagueness (the core claim isn't clear yet).

### Step 2: Classify the claim

Identify which type of claim this is — the type shapes how to challenge it:

- **Causal** — X causes or produces Y ("remote work reduces team cohesion")
- **Predictive** — if X then Y will follow ("AI will commoditize most knowledge work within 5 years")
- **Normative** — X is better/worse/right/wrong ("teams should default to async communication")
- **Definitional** — X is best understood as Y ("a good strategy is a focused bet, not a set of goals")

State the type and ask: "Does that framing feel right, or is this a different kind of claim?"

### Step 3: Sharpen scope

Ask at least one of these before moving on (choose based on the claim type):
- "Who is this true for, and who might it not apply to?"
- "Under what conditions does this hold? When would it break?"
- "Is this always true, sometimes true, or true in specific contexts?"

Don't proceed until the idea has a crisp one-sentence form the user endorses.

---

## Phase 2 — Assumption Mapping

Goal: Surface the beliefs that must be true for the idea to hold. Hidden assumptions are where ideas usually fail.

### Step 1: Ask the user first

**"What has to be true for this to work?"**

Let them list assumptions. Don't interrupt. After they finish, ask: "Anything else?"

### Step 2: Add what they missed

Identify 2–3 additional assumptions the user didn't name — drawn from the stated idea, not invented. Surface them as observations, not corrections:

- "It also seems like this assumes [X]. Does that feel right?"

### Step 3: Stress-test each assumption

For the assumptions on the table, ask:
- "How confident are you in this one?"
- "What would it take to falsify it — what evidence would tell you this assumption is wrong?"

### Step 4: Flag the load-bearing assumption

Identify the weakest or least-examined assumption — the one the idea depends on most but has the least support for. Name it explicitly:

**"The assumption this most depends on is [X]. If that's wrong, the whole idea shifts. How solid is that one?"**

Spend extra time here if needed. This is usually the most valuable conversation.

---

## Phase 3 — Vault Connections

Goal: Bring the user's existing thinking to bear. Notes they've already written may support, extend, or complicate the idea.

### Step 1: Search for related notes

Identify 2–3 key concepts from the stated idea. For each, search via Bash:
```
obsidian search query="<concept>"
```

Read any notes that look genuinely relevant — not just keyword matches.

### Step 2: Sort into two buckets

Present findings clearly:

**Supports** — notes that reinforce the idea, share a mechanism, or come to similar conclusions in adjacent contexts

**Challenges** — notes that complicate the idea, point in a different direction, or add friction to one of the assumptions

For each note, give one sentence on why it's relevant.

### Step 3: Discuss

Ask the user: "Does anything here change how you're thinking about the idea?"

If a vault note directly counters an assumption from Phase 2 — call that out explicitly. If nothing relevant surfaces, say so plainly rather than forcing weak connections.

---

## Phase 4 — Sharpening

Goal: Produce a refined version of the idea that has survived the previous phases.

### Step 1: Restate

Synthesize what emerged. Offer a revised one-sentence version of the idea that incorporates:
- Any scope corrections from Phase 1
- Qualifiers warranted by weak assumptions from Phase 2
- Nuance from vault connections in Phase 3

### Step 2: Check

Ask: **"Is this the idea you set out with, or something better?"**

If the idea changed substantially — that's success. If it survived mostly intact, that's also worth noting: "The idea held up well. The main thing that strengthened it was [X]."

If the user wants to keep refining, stay in this phase.

---

## Phase 5 — Optional Note Capture

Goal: Persist the refined idea if the user wants it. This is optional — the thinking itself is the outcome.

Ask: **"Want to save this as a permanent note?"**

### If yes: generate the note

- **Title**: the refined one-sentence idea, ~8 words or less
- **Body**: the core argument, the load-bearing assumption, key connections
  - Prefer bullet points over comma-delimited lists
  - Keep sentences short unless complexity requires
- **Links**: wrap referenced note titles and any forward-reference concepts in `[[ ]]`; embed links inline in context using pipe syntax — the surrounding words should explain why the connection exists:
  ```
  A broken [[A data stack exists to make data useful, not just store it|data stack]] produces bad AI outputs.
  ```
  Never use a "See also" list — that form loses the relationship context.
- **Tags**: apply tags in YAML frontmatter using the existing vault convention (no `#` prefix):
  ```yaml
  ---
  tags:
    - principle
  ---
  ```
  Retrieve existing tags first:
  ```
  obsidian tags counts
  ```
  Only use existing tags. If a new tag seems warranted, propose it to the user before adding.

### Review before saving

Present the note to the user. Ask:
- "Does this sound like how *you* think about this, or does it feel like a summary of our conversation?"
- "Any word choice or framing you'd change?"

Revise based on their feedback. The note should sound like the user's thinking, not a transcript.

### Save

Once the user is satisfied, save to:
```
03-Resources/Learning/Permanent Notes/<Note Title>.md
```

### If no: end conversationally

Close naturally. No file is written.
