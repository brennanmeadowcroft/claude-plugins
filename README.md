# claude-plugins

## Installation

### 1. Add the marketplace

**Claude Code**
```
/plugin marketplace add brennanmeadowcroft/claude-plugins
```

**Claude Desktop**
1. Click the "+" on a new chat
2. "Connectors" > "Manage Connectors"
3. "Browse Plugins" in the sidebar
4. Click the "Personal" tab
5. Click the "+"
6. Choose add from Github
7. Add `brennanmeadowcroft/claude-plugins` as the repo

**Manual configuration**

You can also add the marketplace directly in `~/.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "bmeadowcroft-plugins": {
      "source": { "source": "github", "repo": "brennanmeadowcroft/claude-plugins" }
    }
  }
}
```

### 2. Install a plugin

**Claude Code**
```
/plugin install <plugin-name>@bmeadowcroft-plugins
```

For example:
```
/plugin install research-toolkit@bmeadowcroft-plugins
```

## Local development

To test a plugin without pushing to GitHub, add your local clone as a marketplace:

```
/plugin marketplace add /path/to/claude-plugins
```

Then install from it:

```
/plugin install <plugin-name>@bmeadowcroft-plugins
```

The marketplace name `bmeadowcroft-plugins` comes from the `name` field in `.claude-plugin/marketplace.json`. Changes to skill and agent files are picked up on the next session — no reinstall needed.

## Plugins

| Plugin                                              | Description                                                                 |
| --------------------------------------------------- | --------------------------------------------------------------------------- |
| [research-toolkit](research-toolkit/README.md)      | Web and Youtube research agents with vector store integration               |
| [development-tools](development-workflow/README.md) | Skills and agents to support the development workflow                       |
| [security-tools](security-tools/README.md)          | Security review agents and dependency scanning for vulnerability detection  |
| [vue-tools](vue-tools/)                             | Vue.js architecture guidance, component design patterns, and best practices |
| [orientation-tools](orientation-tools/)             | Skills to help learn a codebase quickly                                     |
| [chief-of-staff](chief-of-staff/README.md)          | AI executive assistant — daily briefings, weekly planning, and project tracking |
| [exec-assistant](exec-assistant/)                   | Autonomous Todoist task monitor — polls for @claude tasks and dispatches agents |

## Building plugins

Some plugins require a local build step to produce a `.plugin` file. Compiled `.plugin` files are excluded from the repo.

```bash
cd chief-of-staff && ./build-plugin.sh
cd exec-assistant && ./build-plugin.sh
```

## Todoist integration

The `chief-of-staff` and `exec-assistant` plugins use the [official Todoist MCP server](https://todoist.com/help/articles/use-ai-tools-with-todoist). Register it once in Claude Code and both plugins will have access automatically:

```bash
claude mcp add --transport http todoist https://ai.todoist.net/mcp
```

You'll be prompted to authenticate with your Todoist account on first use.
