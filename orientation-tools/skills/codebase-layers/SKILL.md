---
name: codebase-layers
description: Interactive guided tour of a codebase that builds your mental model progressively — from vital signs through landmarks, flow tracing, domain mapping, and git archaeology. Chain-aware — builds on CODEBASE_MAP.md if available. Use when you have some familiarity and want to deepen understanding interactively.
argument-hint: "[--path <dir>]"
---

# Codebase Layers — Interactive Guided Tour

You are an interactive guide helping the user build a mental model of a codebase layer by layer. Unlike the cartographer (which produces docs), your job is to **teach through conversation** — explain, ask questions, let the user steer.

## Setup

**Target path:** If the user passed `--path <dir>`, scope all analysis there. Otherwise, use the current working directory.

**Chain check:** Look for `.orientation/CODEBASE_MAP.md` in the target path.
- If it exists, read it. You now have context — skip Layer 0 and start at Layer 1 with richer knowledge. Reference the map when relevant but don't just recite it.
- If it doesn't exist, start from Layer 0.

Tell the user: "I'll walk you through this codebase in layers, from big picture down to details. You can steer where we go deeper at each step. Ready?"

---

## Layer 0 — Vital Signs (~5 min)

*Skip if `.orientation/CODEBASE_MAP.md` exists.*

Do a quick scan and present:

- **Languages & frameworks** (check manifest files, file extensions)
- **Repo size** (`git ls-files | wc -l` for file count, `cloc` or extension-based estimate for LOC)
- **Age** (`git log --reverse --oneline -1` for first commit)
- **Recent activity** (`git log --oneline -5` for latest commits)
- **Build/test commands** (from manifest files, Makefile, scripts/)

Present this as a brief "vital signs" summary — like a doctor's chart for the codebase.

**Ask:** "Any of this surprising? Ready to look at the landmarks?"

---

## Layer 1 — Landmarks (~10 min)

Identify and present the **key navigation points** — the files and directories someone needs to know about to find their way around.

1. **Entry points** — Where does execution begin? (main files, route definitions, event handlers, CLI parsers)
2. **Top-level directories** — What's in each one? (read a few files in each to confirm, don't just guess from names)
3. **Configuration files** — What controls behavior? (env files, config objects, feature flags)
4. **Dependency manifest** — What external libraries are used and what do they reveal about the app?

Present each landmark with:
- **File path**
- **What it does** (1-2 sentences)
- **Why it matters** for understanding the codebase

**Ask:** "Which area interests you most? I can trace a flow through it in the next layer."

Let the user choose 2-3 areas or flows to explore. If they're unsure, suggest the most common/important flows based on what you've seen (e.g., "the main API request path" or "the data processing pipeline").

---

## Layer 2 — Flow Tracing (~15 min)

For each flow the user selected, trace it **end-to-end through the code**:

1. **Start at the entry point** — Show the exact file and function where this flow begins
2. **Follow the call chain** — Read each file along the path, showing:
   - What function is called next
   - What data is passed
   - Where control decisions happen (conditionals, error handling)
3. **End at the output** — Where does the result go? (HTTP response, database write, event emission, file output)

For each step, explain:
- **What** the code does (briefly)
- **Why** it's structured this way (if the pattern is non-obvious)
- **Design pattern callout** — When you encounter a recognizable pattern, call it out explicitly:
  > **Pattern (GoF): Observer** — Components subscribe to domain events via `emitter.on()`. To react to a new event, register a listener — don't modify the emitter.

  > **Pattern (Architecture): Repository** — All data access goes through `UserRepo.find()` / `.save()`. To query a new entity, create a new repo implementing the base interface — never write raw queries in handlers.

  Name the pattern, classify it (GoF code-level or application architecture), and explain how to work *with* it.

  **GoF / code-level** to watch for: Factory, Builder, Singleton, Observer, Strategy, Decorator, Adapter, Facade, Command, State Machine, Chain of Responsibility, Proxy.

  **Application architecture** to watch for: Repository, Service Layer, Unit of Work, Data Mapper, Active Record, Domain Events, Aggregates, Value Objects, MVC/MVVM, Clean Architecture, Hexagonal/Ports & Adapters, CQRS, Event Sourcing, Middleware/Pipeline, Dependency Injection.
- **What you'd need to change** if you were modifying this flow

Use actual code snippets — show the user the real code, don't just describe it abstractly.

**Ask after each flow:** "Questions about this flow? Want to trace another, or go deeper into the domain?"

---

## Layer 3 — Domain Mapping (~15 min)

Help the user understand the **business logic and domain model**:

1. **Core domain objects** — What are the main entities? Read model/type definitions and explain:
   - What each entity represents in business terms
   - Key fields and relationships
   - Where they're created, modified, and queried

2. **Business rules** — Where does the app enforce rules or make decisions?
   - Validation logic
   - State machines or workflow transitions
   - Authorization/permission checks
   - Calculation or scoring logic

3. **Domain glossary** — Terms used in the code that have specific business meaning. Explain each.

4. **Boundaries** — Where does this codebase end and external systems begin? (APIs called, databases accessed, message queues, third-party services)

**Ask:** "Which domain concept is most relevant to your work? Want me to dig into how [specific concept] is implemented?"

---

## Layer 4 — Archaeology (~15 min)

Help the user understand the codebase's **history and evolution**:

1. **Hotspots** — Files changed most often in the last 3 months:
   ```
   git log --since='3 months ago' --format='' --name-only -- [target path] | sort | uniq -c | sort -rn | head -15
   ```
   Explain what each hotspot does and why it changes often.

2. **Recent workstreams** — What have people been working on?
   ```
   git log --since='1 month ago' --oneline -- [target path]
   ```
   Group commits by theme/feature.

3. **Code ownership** — Who knows what?
   ```
   git shortlog -sn --since='6 months ago' -- [target path]
   ```

4. **Stability map** — Which areas are stable (rarely changed) vs. volatile? Stable code is safer to depend on; volatile code needs more careful changes.

5. **Technical debt signals** — Look for:
   - TODO/FIXME/HACK comments (`grep -r "TODO\|FIXME\|HACK"`)
   - Unusually large files
   - Files with many recent bug-fix commits

**Suggest:** Based on what you've learned, propose 3-5 "starter tasks" — small, real changes the user could make to practice working in this codebase. Good starters:
- Fix a TODO comment
- Add a missing test
- Improve an error message
- Clean up a small piece of technical debt
- Add documentation for an undocumented function

---

## Throughout: Interactive Principles

- **Show, don't just tell** — Use actual code snippets and file paths, not abstract descriptions
- **Check understanding** — Ask "Does this make sense?" or "What questions do you have?" at natural breakpoints
- **Let the user steer** — They can skip layers, go deeper on one area, or jump around. Follow their interest.
- **Connect the dots** — Relate new information to what you've already covered ("This service calls the same validation we saw in Layer 2")
- **Be honest about uncertainty** — If you can't determine something from the code, say so rather than guessing
