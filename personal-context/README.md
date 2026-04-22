# Personal Context

Infrastructure MCP server for Claude Code plugins. Provides a structured contact directory and personal preference files — who you work with, how you communicate, your role and goals — so any plugin can consult "you" without knowing anything about each other.

This is not a skill plugin. It exposes five MCP tools that other plugins (exec-assistant, project-manager, chief-of-staff) call automatically during their workflows.

---

## How It Works

The server reads from `~/.claude-personal/context/` on every tool call, so edits take effect immediately without restarting anything. Two types of data live there:

- **`contacts.yaml`** — a structured people directory (name, email, aliases, team, direct report flag)
- **`*.md` files** — personal context documents, one per topic (communication style, role, preferences, etc.)

---

## Installation

### 1. Prerequisites

Requires `uv` (Python package manager). Install it if not already present:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install the plugin

```bash
claude /plugin install /path/to/claude-plugins --plugin personal-context
```

The plugin registers the MCP server automatically via `.mcp.json` using `uv run` — no manual server setup required.

### 3. Create the context directory

```bash
mkdir -p ~/.claude-personal/context
```

### 4. Add a contacts file

Create `~/.claude-personal/context/contacts.yaml`:

```yaml
people:
  - name: Alice Smith
    email: alice.smith@company.com
    aliases: [Alice]
    team: Engineering
    is_direct_report: true
    notes: Staff engineer, owns the API platform

  - name: Bob Johnson
    email: bjohnson@company.com
    aliases: [Bob, BJ]
    team: Product
    notes: PM for the growth squad

  - name: Carolyn Lee
    email: carolyn@company.com
    aliases: [Carolyn, Carol]
    team: Design
```

**Supported fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Full canonical name — used for Obsidian `[[wiki links]]` |
| `email` | Yes | Used by `lookup_contact` for calendar event resolution |
| `aliases` | No | First names, nicknames, or initials the person goes by |
| `team` | No | Team or org context |
| `is_direct_report` | No | `true` if this person reports to you — enables direct report check-in in meeting notes |
| `notes` | No | Freeform context surfaced to skills |

### 5. Add personal context files (optional)

Drop any `.md` files into `~/.claude-personal/context/`. Each filename becomes a topic key that skills can retrieve with `get_context_file`. Common examples:

```
~/.claude-personal/context/
  communication-style.md        ← how you write emails, preferred tone
  role-and-responsibilities.md  ← your title, team, what you own
  goals-and-priorities.md       ← current OKRs or focus areas
  preferences.md                ← working style, meeting norms, etc.
```

Write these in first person. Skills read them verbatim when drafting communications or preparing context for meetings.

---

## MCP Tools

Once installed, these tools are available to any plugin running in the same Claude Code session:

| Tool | Description |
|------|-------------|
| `lookup_contact(email)` | Find a contact by email address (case-insensitive) |
| `find_contact(query)` | Find a contact by full name, alias, or partial name |
| `list_contacts()` | Return all contacts from `contacts.yaml` |
| `get_context_file(topic)` | Read a context markdown file by topic name (e.g. `"communication-style"`) |
| `list_context_files()` | Return a list of all available context topic names |

`find_contact` resolves in order: exact name match → alias match → partial name match.

---

## Tips

**Keep contact names canonical.** The `name` field is used to generate Obsidian `[[wiki links]]` — make sure it matches the filename you use for meeting notes (e.g. if your note file is `Alice Smith - 2026.md`, the name should be `Alice Smith`).

**`is_direct_report` unlocks the check-in section.** When this is `true`, meeting note prep automatically includes a Direct Report Check-in section with engagement pulse tracking, skills development, and quarterly goals.

**Context files re-read on every call.** Edit `communication-style.md` or `contacts.yaml` at any time — the next skill invocation picks up the changes without restarting Claude Code.
