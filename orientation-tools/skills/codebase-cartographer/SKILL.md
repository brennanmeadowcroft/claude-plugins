---
name: codebase-cartographer
description: Automated parallel scan of a codebase that produces CODEBASE_MAP.md and ORIENTATION.md reference documents in the .orientation/ folder. Explores structure, domain concepts, git history, and generates a dependency diagram. Use when first encountering an unfamiliar codebase.
argument-hint: "[--path <dir>]"
---

# Codebase Cartographer

You are mapping an unfamiliar codebase to produce reference documentation that helps a developer orient quickly and start contributing.

## Step 1: Determine scope

If the user passed `--path <dir>`, scope ALL analysis to that directory. Otherwise, use the current working directory.

Store:
- `TARGET` — the target directory path
- `BASENAME` — the basename of `TARGET` (e.g. `my-project`)
- `TODAY` — today's date (YYYY-MM-DD)

All file references in output docs should be relative to `TARGET`. All output files go to `TARGET/.orientation/`. Create that directory now if it does not exist.

## Step 2: Quick detection

Before launching parallel exploration, do a fast scan to identify the tech stack. Check for:

- `package.json`, `tsconfig.json` → TypeScript/JavaScript (prefer TypeScript label if `tsconfig.json` present)
- `Cargo.toml` → Rust
- `go.mod` → Go
- `pyproject.toml`, `setup.py`, `requirements.txt` → Python
- `pom.xml`, `build.gradle` → Java/Kotlin
- `Gemfile` → Ruby
- `Dockerfile`, `docker-compose.yml` → Containerized
- `README.md`, `CLAUDE.md` → Existing documentation
- `.github/`, `.gitlab-ci.yml` → CI/CD

Store the detected stack — this is used in Step 5 for diagram generation.

## Step 3: Parallel exploration

Launch **3 Explore agents in parallel** (use the Agent tool with subagent_type "Explore"), each with a specific focus. Provide each agent with `TARGET` and the tech stack from Step 2.

### Agent 1 — Structure & Stack

Prompt: "Explore the codebase at [TARGET] to map its structure. This is a [tech stack] project. Find and report:
1. The complete directory tree (top 2-3 levels, noting purpose of each directory)
2. Entry points (main files, route definitions, event handlers, CLI entry points)
3. Build system and configuration (how to build, run, and test)
4. CI/CD configuration
5. Key configuration files and what they control
6. Test setup (framework, test file locations, how to run tests)
7. External dependencies that reveal what the app does (scan dependency manifest files)
Be thorough — read key files, not just filenames."

### Agent 2 — Domain & Patterns

Prompt: "Explore the codebase at [TARGET] to understand its domain and design patterns. This is a [tech stack] project. Find and report:
1. Data models, types, schemas, and interfaces — what are the core domain objects?
2. API routes or endpoints — what operations does the system expose?
3. Business logic location — where do the 'rules' live?
4. **Design patterns** — Identify specific, named patterns at two levels:

   **GoF / code-level patterns** (how individual classes/modules are structured):
   Factory, Builder, Singleton, Observer/Event Emitter, Strategy, Decorator, Adapter, Facade, Command, State Machine, Iterator, Proxy, Chain of Responsibility

   **Application architecture patterns** (how the app is organized internally):
   - Fowler's PoEAA: Repository, Unit of Work, Active Record, Data Mapper, Service Layer, Gateway
   - DDD: Aggregates, Bounded Contexts, Value Objects, Entities, Domain Events, Domain Services
   - Structural: MVC/MVVM/MVP, Clean Architecture, Hexagonal/Ports & Adapters, CQRS, Event Sourcing, Middleware/Pipeline, Dependency Injection

   For each pattern found, report:
   - The pattern name and which category it belongs to (GoF or application architecture)
   - The file(s) where it's implemented
   - A concrete example (function name, class name, or code snippet)
   - How to extend it (e.g., 'add a new case to the switch' or 'implement the interface')
   Only report patterns you can point to in the code — don't guess or force-fit.
5. Naming conventions and code organization style
6. Key abstractions — what are the main classes/modules/functions and how do they relate?
7. Domain glossary — business terms used in the code and what they mean
Read the actual code in key files, not just filenames. Look at models, services, handlers, and types."

### Agent 3 — History & Hotspots

Prompt: "Analyze the git history of the codebase at [TARGET] to understand its evolution. Run these git commands and report findings:
1. `git log --oneline -30` — recent commit messages (what's been worked on lately?)
2. `git log --format='%aN' | sort | uniq -c | sort -rn | head -10` — top contributors
3. `git log --since='3 months ago' --format='' --name-only | sort | uniq -c | sort -rn | head -20` — most-changed files in last 3 months (hotspots)
4. `git log --since='1 month ago' --oneline` — last month's activity summary
5. `git log --diff-filter=A --format='' --name-only | wc -l` vs `git ls-files | wc -l` — rough sense of codebase growth
6. Look at recent merge commits or PR-style messages to understand current workstreams
Scope all git commands to [TARGET] using `-- [TARGET]` where applicable.
Summarize: What areas are actively evolving? What areas are stable? Who works on what?"

## Step 4: Synthesize into `.orientation/CODEBASE_MAP.md`

Combine findings from all three agents into a structured reference document. Write it to `[TARGET]/.orientation/CODEBASE_MAP.md`.

Use this template:

```markdown
# Codebase Map

> Auto-generated by `/codebase-cartographer` on [TODAY]. This is a reference document — not a substitute for reading the code.

## Tech Stack

[Language, framework, key libraries — 2-3 lines max]

## Directory Structure

[Annotated directory tree, 2-3 levels deep. Each directory gets a one-line purpose annotation.]

## Key Entry Points

[List the main entry points with file paths and what they do]

## Core Domain Concepts

[Table mapping business terms to code locations]

| Concept | Code Location | Description |
|---------|--------------|-------------|

## Data Flow

[How a typical request/operation flows through the system. Use a simple text diagram or numbered steps.]

## Internal Dependencies

[Which modules depend on which. Focus on the major groupings, not every import.]

[If a dependency diagram was generated in Step 5, add: "See `.orientation/dependency-graph.svg` for a generated module dependency diagram."]

## Design Patterns Identified

### GoF / Code-Level Patterns

| Pattern | Where Used | Example | How to Extend |
|---------|-----------|---------|---------------|

### Application Architecture Patterns

| Pattern | Where Used | Example | How to Extend |
|---------|-----------|---------|---------------|

Only list patterns actually found in the code. For each, note the canonical example and how to extend it.

## Naming Conventions & Code Style

[Naming conventions, file organization style, code style patterns observed]

## Git Hotspots

[Most-changed files, active development areas, recent workstreams]

## Key Files Quick Reference

| File | Why It Matters |
|------|---------------|
```

**Note:** Write CODEBASE_MAP.md now with a placeholder in the Internal Dependencies section: `[Dependency diagram: attempting generation — see Step 5]`. You will update this line after Step 5.

## Step 5: Attempt dependency diagram generation

Based on the detected stack from Step 2, attempt to generate a module dependency diagram. Output to `[TARGET]/.orientation/dependency-graph.svg`.

If `dot` (Graphviz) is not available (`command -v dot` fails), skip this step entirely and set `diagram_generated=false`.

Otherwise, run the appropriate command for the detected stack:

**TypeScript/JS:**
```bash
cd [TARGET] && npx --no dependency-cruiser --include-only "^src" --output-type dot . 2>/dev/null | dot -Tsvg -o .orientation/dependency-graph.svg
```
If `src/` does not exist, try without the `--include-only` flag scoped to the main source directory.

**Python:**
```bash
cd [TARGET] && pyreverse -o dot -p project . 2>/dev/null
# pyreverse writes packages_project.dot and classes_project.dot to cwd
dot -Tsvg packages_project.dot -o .orientation/dependency-graph.svg 2>/dev/null
rm -f packages_project.dot classes_project.dot
```

**Go:**
```bash
cd [TARGET] && goda graph ./... 2>/dev/null | dot -Tsvg -o .orientation/dependency-graph.svg
```

**Other stacks:** Skip and set `diagram_generated=false`.

If the command fails or produces an empty file, set `diagram_generated=false` and move on silently.

If successful (`diagram_generated=true`): update the placeholder line in `.orientation/CODEBASE_MAP.md`'s Internal Dependencies section to:
```
See `.orientation/dependency-graph.svg` for a generated module dependency diagram.
```

If unsuccessful: remove the placeholder line from CODEBASE_MAP.md.

## Step 6: Synthesize into `.orientation/ORIENTATION.md`

Write a narrative guide to `[TARGET]/.orientation/ORIENTATION.md`.

Use this template:

```markdown
# Orientation Guide

> Auto-generated by `/codebase-cartographer` on [TODAY].

## What This Project Does

[2-3 sentence summary of the project's purpose, based on what you found in code, docs, and domain analysis]

## Architecture at a Glance

[Architecture style (monolith, microservices, serverless, etc.), key layers, how they connect. Keep it to one paragraph.]

## How to Build and Run

[Commands to install dependencies, build, run locally, and run tests. Be specific.]

## Where to Find Things

| I want to... | Look in... |
|--------------|-----------|
| Add a new API endpoint | ... |
| Modify business logic | ... |
| Add a new data model | ... |
| Write a test | ... |
| Change configuration | ... |

## Patterns to Follow

[Key patterns that a new contributor should follow for consistency. Include brief code examples if helpful.]

## Gotchas and Non-Obvious Things

[Anything surprising, unusual, or easy to get wrong. Things that aren't obvious from the code structure alone.]

## Active Development Areas

[What's being worked on recently, based on git history. Helps avoid stepping on toes or picking up stale work.]

## Suggested Next Steps

- Run `/codebase-layers` for an interactive guided tour of specific areas
- Run `/codebase-mikado --goal "your task"` when you're ready to trace a specific change
- Run `/codebase-health` before starting a large feature or refactor
```

## Step 7: Write `.orientation/README.md`

Write the orientation index file to `[TARGET]/.orientation/README.md`:

```markdown
# Codebase Orientation: [BASENAME] -- [TODAY]
Orientation to the codebase providing a breakdown of the structure, architecture and relationships. See the following files for specifics.

## Files
| File | Description |
|------|-------------|
| CODEBASE_MAP.md | Structured reference: stack, directory layout, patterns, git hotspots |
| ORIENTATION.md | Narrative guide: what it does, how to build/run, where to find things |
```

If `diagram_generated=true`, append a row:
```
| dependency-graph.svg | Module dependency diagram |
```

If `.orientation/README.md` already exists (from a prior health run), read it first and preserve any existing rows that are not being replaced. Add or update rows for CODEBASE_MAP.md, ORIENTATION.md, and optionally dependency-graph.svg — do not remove a health-report.md row if it exists.

## Step 8: Present summary

After writing all documents, present a brief summary to the user:

1. **One-paragraph overview** of what you found
2. **2-3 things that stand out** (unusual patterns, surprising complexity, notable design choices)
3. **Diagram**: note whether a dependency diagram was generated and where to find it
4. **Suggest next steps**: which areas to explore deeper via `/codebase-layers`, or if they have a task, suggest `/codebase-mikado`

Keep the summary concise — the detailed information is in the docs.
