---
name: thinking-partner
description: Process a piece of content (article, book chapter, video, etc.) into atomic notes for the user's Zettelkasten/Second Brain in Obsidian. Guides the user through understanding the material, surfacing connections to existing notes, and generating well-linked permanent notes. Trigger when the user wants to digest, process, or capture notes from an article, bookmark, or piece of content into their second brain, Zettelkasten, or Obsidian vault. Also trigger on phrases like "let's digest this", "turn this into notes", "process this article", "add this to my second brain", or when the user shares a Karakeep bookmark ID or URL and wants to learn from it. Must be run from the root of the Obsidian vault.
---

# Second Brain Digest

Help the user extract lasting knowledge from a piece of content and turn it into well-connected atomic notes in their Zettelkasten. The goal is not to summarize — it's to help the user genuinely understand the ideas, connect them to what they already know, and generate notes they'll actually return to.

There are three phases. Move through them at the user's pace — Phase 1 in particular should not be rushed.

## Arguments

- `--bookmark <url-or-id>` — a Karakeep bookmark URL or ID to fetch content and highlights from
- `--file <path>` — path to a local file (PDF, markdown, etc.) containing the content to process; the user may also provide highlights or annotations alongside it

If neither argument is provided, ask the user to share the content or point you to it before proceeding.

---

## Phase 1 — Understanding

The aim here is to help the user internalize the ideas, not just catalog them. This is the most valuable part of the whole process.

### Step 1: Fetch content and highlights

**If `--bookmark` is provided:**
Use the Karakeep MCP to fetch the bookmark and its content:
- `mcp__karakeep__get-bookmark` — retrieves metadata and any saved notes/highlights
- `mcp__karakeep__get-bookmark-content` — retrieves the full article content in markdown

**If `--file` is provided:**
Read the file directly. If the user has also provided highlights or annotations (e.g. as a separate file or pasted text), incorporate those as the equivalent of saved highlights.

**If neither is provided:**
Ask the user to share the content before continuing.

### Step 2: Ask the user first

Before sharing your own analysis, ask: **"What ideas stood out to you from this?"**

Let the user lead. Their framing reveals what they found significant and helps you tailor the discussion to their existing mental model.

### Step 3: Extract topics

From the content, identify the most relevant:
- **Concepts** — abstract, reusable ideas that could stand alone as a note. Should be applicable across contexts (e.g. "compounding complexity", not "Snowflake pricing"). These are the core subjects of a discussion.
- **Terms** — definitions worth capturing, especially those that relate to processes, embody frameworks, have competing definitions, or carry meaning across multiple contexts.

Only extract from the content itself. Don't invent entities.

### Step 4: Engage in discussion

Compare the user's ideas against yours. For each idea the user raises:
- If you agree and have nothing to add, affirm and move on
- If the user's framing is different from yours, **ask them to explain it further** — don't just correct them. Their explanation often sharpens the idea
- If they missed something important, introduce it as a question or observation

The discussion should feel like a thinking partnership. Keep probing until the ideas are crisp enough to write down clearly.

When the user seems comfortable with the ideas, or explicitly asks to move on, proceed to Phase 2.

---

## Phase 2 — Connections

Surface relevant existing notes so the new notes can join the network rather than sit in isolation.

### Step 1: Search for related notes

For each key concept, search via Bash:
```
obsidian search query="<concept>"
```

Only surface notes where a real connection exists — not everything that matches a keyword.

### Step 2: Get existing tags

```
obsidian tags counts
```

Note the existing tags and their counts. You'll use these in Phase 3 to apply tags consistently.

### Step 3: Discuss connections

For each potentially related note, ask the user: "Does this seem related to what we're capturing?"

If yes, explore the relationship:
- Is it the same idea in a different context?
- Does one note support or extend the other?
- Would a link make sense in one direction, both, or neither?

The user may also suggest connections you didn't surface — follow their lead.

---

## Phase 3 — Generate Notes

Once the ideas are clear and connections are identified, generate atomic notes.

### Note structure

- **Title**: the idea stated plainly, ~8 words or less
- **Body**: concise support for the idea — easy to scan, not exhaustive
- Prefer bullet points over comma-delimited lists
- Keep sentences short unless complexity requires otherwise
- Quote the source wherever possible — use the author's or article's words over paraphrase

### Linking

Wrap author names, article/book titles, and other note titles in `[[ ]]`.

Embed links **inline in context** using pipe syntax — the surrounding words should explain why the connection exists:
```
A broken [[A data stack exists to make data useful, not just store it|data stack]] produces bad AI outputs.
```

Never use a "See also" list at the bottom — that form loses the relationship context. If a connection doesn't fit naturally into a sentence, it may not be strong enough to include.

Forward-reference links are encouraged — if you reference a concept that doesn't have a note yet, link it anyway to seed future notes:
```
[[Data Pipeline Structure]] determines how quickly hidden complexity compounds.
```

### Tagging

Apply tags in YAML frontmatter — no `#` prefix:
```yaml
---
tags:
  - principle
---
```

Only use tags from the existing convention (retrieved in Phase 2). Tags should be cross-cutting across topics — not topic labels, which are handled by index notes. If a new tag seems warranted, propose it to the user before adding it.

### Review with the user before saving

Present all generated notes to the user before writing any files. When reviewing, ask:
- Does the framing of each note reflect how *you* think about this idea, or does it sound like the source?
- Is there a phrase or word choice you'd change to make it feel more like your own thinking?
- Does anything feel off or need a different angle?

Revise based on their feedback. The notes should sound like the user, informed by the source — not a paraphrase of the author.

### Save notes

Once the user is satisfied, save each note to:
```
03-Resources/Learning/Permanent Notes/<Note Title>.md
```

### Update index notes

After saving, ask: **"Which of these feels like a landmark note worth adding to an index?"**

Index notes are entry points into a topic — they should link to notes that are central or broadly connected, not to every note generated. Add only the landmark-level notes to the relevant index files under `03-Resources/Learning/Index Notes/`.
