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

## Plugins

| Plugin                                              | Description                                                                 |
| --------------------------------------------------- | --------------------------------------------------------------------------- |
| [research-toolkit](research-toolkit/README.md)      | Web and Youtube research agents with vector store integration               |
| [development-tools](development-workflow/README.md) | Skills and agents to support the development workflow                       |
| [security-tools](security-tools/README.md)          | Security review agents and dependency scanning for vulnerability detection  |
| [vue-tools](vue-tools/)                             | Vue.js architecture guidance, component design patterns, and best practices |
| [orientation-tools](orientation-tools/)             | Skills to help learn a codebase quickly                                     |
