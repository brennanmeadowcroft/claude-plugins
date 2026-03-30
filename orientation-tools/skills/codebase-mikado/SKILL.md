---
name: codebase-mikado
description: Task-driven codebase learning using the Mikado method. Given a change goal, traces all dependencies and walks you through everything you need to understand to make the change safely. Chain-aware — uses CODEBASE_MAP.md if available. Use when you have a specific task and want to learn just enough to execute it.
argument-hint: "--goal <description> [--path <dir>]"
---

# Codebase Mikado — Task-Driven Dependency Tracing

You are helping the user learn a codebase through the lens of a specific change they want to make, using the Mikado method. Instead of mapping everything, you trace exactly what they need to understand to make their change safely and confidently.

## Setup

**Target path:** If the user passed `--path <dir>`, scope all analysis there. Otherwise, use the current working directory.

**Change goal:** The user should provide a `--goal` describing what they want to change. Examples:
- `--goal "add input validation to the /api/submit endpoint"`
- `--goal "fix the race condition in the queue processor"`
- `--goal "add a new field to the user model"`

If no goal is provided, help the user define one:
1. Check for `.orientation/CODEBASE_MAP.md` — if it exists, read it and suggest goals based on active development areas or TODOs
2. Check for TODO/FIXME comments in the codebase
3. Check recent git history for in-progress work
4. Ask the user: "What change would you like to make? Or I can suggest a good starter task."

**Chain check:** Look for `.orientation/CODEBASE_MAP.md` in the target path. If it exists, read it — use it to quickly locate relevant areas instead of searching from scratch.

---

## Phase 1: Locate the Starting Point

Based on the goal, identify the **primary file(s)** that would need to change.

Search strategy:
1. If `.orientation/CODEBASE_MAP.md` exists, use the "Key Files" and "Directory Structure" sections to narrow your search
2. Search for keywords from the goal (endpoint names, function names, model names)
3. Grep for related strings in the codebase
4. Check route definitions, model files, test files for relevant matches

Present to the user:
> **Starting point for "[goal]":**
> The main file(s) you'd modify: `[path/to/file.ext]` (lines X-Y)
> [Brief description of what this code currently does]

---

## Phase 2: Dependency Discovery

For each file identified as needing changes, systematically discover what you need to understand. Read the file and ask these questions:

### Direct Dependencies
- What does this file **import**? Read those imports to understand the interfaces.
- What **functions/methods** would you modify? What do they call?
- What **types/interfaces** are involved? Where are they defined?

### Upstream Dependencies (what calls this code)
- What other files **import this module**? (`grep -r "import.*from.*[module]"` or equivalent)
- What **routes or handlers** invoke this code?
- What would **break** if you changed the interface?

### Test Dependencies
- What **test files** cover this code? (`find . -name "*.test.*" -o -name "*_test.*"` near the source)
- What **test patterns** are used? (mocking, fixtures, integration tests)
- How do you **run just these tests**?

### Configuration Dependencies
- Does this code read **environment variables** or **config**?
- Are there **feature flags** that control this behavior?
- Are there **database migrations** involved?

---

## Phase 3: Build the Mikado Graph

Present the dependency tree as a visual graph. Use indentation to show the hierarchy:

```
Goal: [user's goal description]
│
├── MODIFY: path/to/primary-file.ext
│   ├── UNDERSTAND: path/to/imported-module.ext — [what it provides]
│   │   └── UNDERSTAND: path/to/types.ext — [type definitions used]
│   ├── UNDERSTAND: path/to/service.ext — [business logic this calls]
│   │   ├── UNDERSTAND: path/to/repository.ext — [data access layer]
│   │   └── UNDERSTAND: path/to/validator.ext — [validation patterns to follow]
│   └── UPDATE: path/to/tests/primary-file.test.ext — [existing test patterns]
│
├── CHECK: path/to/upstream-caller.ext — [calls the code you're changing]
│   └── VERIFY: No interface change needed, or update call site
│
└── FOLLOW: path/to/related-config.ext — [configuration that affects behavior]
```

**Node types:**
- **MODIFY** — Files you'll directly change
- **UNDERSTAND** — Files you need to read to make your change correctly
- **UPDATE** — Files that need corresponding changes (tests, docs)
- **CHECK** — Files that might be affected — verify they still work
- **FOLLOW** — Configuration or setup that influences behavior

---

## Phase 4: Bottom-Up Walkthrough

Starting from the **leaf nodes** (deepest dependencies) and working up toward the goal, walk the user through each node:

For each node, explain:

1. **What this file/module does** — 2-3 sentence summary
2. **The specific part relevant to your goal** — Show the actual code (with line numbers)
3. **Key patterns to follow** — How does existing code in this area work? What conventions should you match?
4. **Gotchas** — Anything non-obvious, error-prone, or easy to get wrong
5. **Connection to parent** — How does this connect to the next level up in the graph?

Use actual code snippets. Show the real interfaces, real function signatures, real patterns.

**Check in periodically:** "Does this make sense? Questions before we move up to the next level?"

---

## Phase 5: Implementation Summary

After walking through all nodes, present a clear implementation plan:

### What You Now Know
[Brief summary of the key things the user learned during the walkthrough]

### Implementation Order
[Numbered list of changes to make, in the order they should be done — leaves first, goal last]

1. **First:** [Leaf-level change or preparation] — `path/to/file.ext`
2. **Then:** [Next dependency] — `path/to/file.ext`
3. **Then:** [Primary change] — `path/to/file.ext`
4. **Finally:** [Update tests] — `path/to/tests/file.test.ext`

### Patterns to Match
[Key conventions to follow, with code examples from the existing codebase]

### What to Test
[How to verify the change works — specific test commands, manual verification steps]

### Risks and Edge Cases
[Things that could go wrong, edge cases to handle, areas where extra care is needed]

---

## Throughout: Mikado Principles

- **Just enough, not everything** — Only trace dependencies relevant to the goal. Don't map the whole codebase.
- **Show the real code** — Use actual file paths, line numbers, and code snippets. Abstract descriptions don't build understanding.
- **Bottom-up builds confidence** — By the time you reach the goal, the user should understand everything it depends on.
- **Name the unknowns** — If something is unclear from the code alone (e.g., business context), say so and ask.
- **Keep the graph visible** — Reference the Mikado graph throughout so the user knows where they are in the tree.
- **Practical over theoretical** — Focus on "what do I need to know to make this change" not "how does everything work."
