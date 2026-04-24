---
name: track-decision
description: Explicitly capture a decision or disposition to memory so CoS skills don't re-surface it. Use when the user says "remember that...", "track a decision...", "note that I don't need X", or invokes /track-decision. Must be run from the root of the Obsidian vault.
---

# Track Decision

Capture a decision or disposition to the appropriate decisions file so it persists across sessions.

## Arguments

- `--text "..."` — the decision to record (required)
- `--category <type>` — one of: `email`, `task`, `approach`, `process`, `strategic` (sets TTL tier; defaults to `approach` if omitted)
- `--ttl quick|tactical|strategic` — override TTL tier
- `--days N` — set an exact TTL in days
- `--project <folder>` — write to `01-Projects/<folder>/decisions.yaml` instead of the global file

## TTL Tiers

| Tier | Days | Default for |
|------|------|-------------|
| quick | 7 | email, task |
| tactical | 21 | approach, process |
| strategic | 90 | strategic |

## Steps

1. **Determine TTL in days:**
   - If `--days N` is given, use N directly.
   - If `--ttl` is given, map to tier (quick→7, tactical→21, strategic→90).
   - Otherwise derive from `--category`:
     - `email` or `task` → 7 days (quick)
     - `approach` or `process` → 21 days (tactical)
     - `strategic` → 90 days (strategic)
     - No category → 21 days (tactical default)

2. **Determine target file:**
   - If `--project <folder>` is given → `01-Projects/<folder>/decisions.yaml`
   - Otherwise → `decisions.yaml` at vault root

3. **Generate entry:**
   - ID: `dec_<YYYYMMDD>_<4 random hex chars>` (use `date +%Y%m%d` and `python3 -c "import secrets; print(secrets.token_hex(2))"` or similar)
   - `created`: today's date in `YYYY-MM-DD` format
   - `expires`: today + TTL days

4. **Write entry** — append to the target YAML file. If the file doesn't exist, create it with the entry as the first element. Preserve all existing entries exactly. Use this format:

```yaml
- id: dec_20260422_a1b2
  text: "The decision text verbatim"
  category: approach
  created: 2026-04-22
  expires: 2026-05-13
```

   Read the file first (if it exists), parse the YAML list, append the new entry, and write back with `yaml.dump(..., default_flow_style=False, allow_unicode=True, sort_keys=False)`. If PyYAML is unavailable, append a raw YAML block manually using Bash heredoc.

5. **Confirm** with one short line: "Tracked: '[text]' — expires [expires date] · saved to [file]." No more detail than that.

## Scope Heuristics (when `--project` is not specified)

- Categories `email` and `task` → always global (`decisions.yaml`)
- Categories `approach`, `process`, `strategic` → project-scoped if `--project` is given, otherwise global
- If the user's phrasing makes project scope obvious (e.g., "for the api-redesign project, we decided…") but they didn't pass `--project`, ask once: "Should I save that to `01-Projects/api-redesign/decisions.yaml` or globally?"

## Quality Notes

- Don't echo the entry back in YAML — one confirmation sentence is enough.
- Don't ask about TTL unless the user explicitly wants to override it — derive it from category.
- If the target project folder doesn't exist, warn the user before creating the file: "I don't see a folder at `01-Projects/<folder>/` — should I create the decisions file there anyway?"
