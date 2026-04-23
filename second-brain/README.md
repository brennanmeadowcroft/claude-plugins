# thinking-partner

A thinking partner that helps you digest content — articles, book chapters, videos — into well-connected atomic notes in your Obsidian Zettelkasten. Fetches content and highlights from Karakeep bookmarks, guides you through understanding and connecting ideas, then generates and saves permanent notes to your vault.

## Prerequisites

- [1Password desktop app](https://1password.com/downloads/) — must be installed and signed in
- [1Password CLI](https://developer.1password.com/docs/cli/get-started/) (`op`)
- [Node.js](https://nodejs.org/) (for `npx`)
- Obsidian vault — run this skill from the vault root

## Setup

### 1. Install the 1Password CLI

```sh
brew install 1password-cli
```

Verify with `op --version`. Sign in via the desktop app integration — no separate `op signin` needed if the desktop app is installed.

### 2. Add your Karakeep credentials to 1Password

Create an item named **Karakeep** in your **Personal** vault with these fields:

| Field name | Value |
|---|---|
| `url` | Your Karakeep server URL (e.g. `https://karakeep.example.com`) |
| `api-key` | Your Karakeep API key (Settings → API Keys) |

### 3. Create the env reference file

Create `~/.config/karakeep.env` with the following content — these are 1Password references, not secrets, so this file is safe to commit to your dotfiles:

```sh
KARAKEEP_API_ADDR=op://Personal/Karakeep/url
KARAKEEP_API_KEY=op://Personal/Karakeep/api-key
```

If you named the vault or item differently in step 2, adjust the `op://vault/item/field` paths accordingly.

### 4. Enable the plugin

Install and enable `thinking-partner` from the plugin marketplace in Claude Code settings.

## Usage

Run this skill from the root of your Obsidian vault. Invoke it with:

- `/thinking-partner:thinking-partner --bookmark <url-or-id>` — fetch a Karakeep bookmark by URL or ID
- `/thinking-partner:thinking-partner --file <path>` — process a local file (PDF, markdown, etc.)
- `/thinking-partner:thinking-partner` — paste or describe content when prompted

The skill walks you through three phases: **Understanding** (discuss the ideas), **Connections** (surface related notes), and **Generate** (write atomic notes to your vault).
