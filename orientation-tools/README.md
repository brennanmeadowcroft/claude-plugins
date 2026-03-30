# Orientation Tools

The Orientation Tools are intended to help the user get up to speed on a codebase and domain so they are able to contribute without relying entirely on Claude Code.

Supports monorepos through an optional `path` param indicating which area of the code to focus on. If not provided, Claude will use the root of the project.

## Installation
1. Add the marketplace to Claude using the instructions in the project README
2. Add the plugin to claude code with `/plugin install orientation-tools@brennanmeadowcroft/claude-plugins`

It's also possible to install this within a codebase or repo so it's always available. Within `.claude/settings.json`, add the following:
```json
{
  "extraKnownMarketplaces": {
    "orientation-tools": {
      "source": { "source": "github", "repo": "brennanmeadowcroft/claude-plugins", "ref": "v1.0.0" }
    }
  },
  "enabledPlugins": {
    "orientation-tools@brennanmeadowcroft/claude-plugins": true
  }
}
```

## Dependencies

The following tools extend what orientation skills can produce. Run `scripts/check-dependencies.sh` from your project to see what's installed for your stack.

**Universal (required for diagrams and health analysis):**
- `graphviz` — `brew install graphviz`
- `scc` — `brew install scc`

**Language-specific (dependency diagrams):**
- TypeScript/JS: `npx dependency-cruiser`
- Python: `pip install pylint` (includes `pyreverse`)
- Go: `go install github.com/loov/goda@latest`

All tools are optional — skills degrade gracefully if tools are missing.

## Output Files

All skills that produce files write to a `.orientation/` directory in the target path. This keeps orientation artifacts out of the project root and grouped together.

| File                                | Produced by          | Description                                                           |
| ----------------------------------- | -------------------- | --------------------------------------------------------------------- |
| `.orientation/README.md`            | cartographer, health | Auto-generated index of all orientation files                         |
| `.orientation/CODEBASE_MAP.md`      | cartographer         | Structured reference: stack, directory layout, patterns, git hotspots |
| `.orientation/ORIENTATION.md`       | cartographer         | Narrative guide: what it does, how to build/run, where to find things |
| `.orientation/dependency-graph.svg` | cartographer         | Module dependency diagram (generated if tools available)              |
| `.orientation/health-report.md`     | codebase-health      | Complexity × churn analysis identifying high-risk areas               |

## Usage

### Initial Orientation
```
/codebase-orientation [--path <dir>]
```
Entry point if starting on a new codebase. Runs a dependency check, asks questions to understand your situation, and routes to the right skill. Also detects planning intent — if you mention a refactor or large feature, it routes to `/codebase-health` first.

### Specific Skills
```
/codebase-cartographer [--path <dir>]
/codebase-layers [--path <dir>]
/codebase-mikado --goal "<description>" [--path <dir>]
/codebase-health [--path <dir>] [--since <period>]
```
Go straight to any skill if you know what you need.

## Skills

| Skill                    | Description                                                                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `/codebase-orientation`  | Entry point — checks dependencies, assesses your situation, routes to the right skill including health analysis for planned refactors |
| `/codebase-cartographer` | Maps the codebase structure, patterns, and git history; generates a dependency diagram SVG if tools are available                     |
| `/codebase-layers`       | Interactive guided tour building a mental model layer by layer                                                                        |
| `/codebase-mikado`       | Task-driven dependency tracing using the Mikado method                                                                                |
| `/codebase-health`       | Churn + complexity analysis identifying high-risk files before a large feature or refactor                                            |

## Agents

None
