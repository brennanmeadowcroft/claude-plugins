#!/usr/bin/env python3
"""
Injects global decisions (last N days, non-expired) as additionalContext for CoS skills.
Project decisions are NOT loaded here — skills load them when a project is in context.

Runs as a UserPromptSubmit hook scoped to chief-of-staff skill invocations.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path


def read_lookback_days(vault_root: Path) -> int:
    claude_md = vault_root / "CLAUDE.md"
    if not claude_md.exists():
        return 30
    for line in claude_md.read_text().splitlines():
        if "decisions-lookback-days:" in line:
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
    return 30


def main():
    try:
        import yaml
    except ImportError:
        # PyYAML not installed — emit nothing rather than crash
        print(json.dumps({"additionalContext": ""}))
        return

    vault_root = Path(".")
    decisions_file = vault_root / "decisions.yaml"
    if not decisions_file.exists():
        print(json.dumps({"additionalContext": ""}))
        return

    raw = decisions_file.read_text()
    all_entries = yaml.safe_load(raw) or []
    if not isinstance(all_entries, list):
        print(json.dumps({"additionalContext": ""}))
        return

    today = date.today()
    lookback = read_lookback_days(vault_root)
    cutoff = today - timedelta(days=lookback)

    active = []
    has_expired = False

    for d in all_entries:
        if not isinstance(d, dict):
            continue
        created_raw = d.get("created", "2000-01-01")
        expires_raw = d.get("expires")

        try:
            created = date.fromisoformat(str(created_raw))
        except ValueError:
            created = date(2000, 1, 1)

        if expires_raw:
            try:
                expires = date.fromisoformat(str(expires_raw))
            except ValueError:
                expires = None
        else:
            expires = None

        # Skip expired entries (and flag them for pruning)
        if expires and expires < today:
            has_expired = True
            continue

        # Outside lookback window — skip on read but keep in file
        if created < cutoff:
            continue

        active.append((d, expires))

    # Prune expired entries from the file in place
    if has_expired:
        remaining = []
        for d in all_entries:
            if not isinstance(d, dict):
                remaining.append(d)
                continue
            expires_raw = d.get("expires")
            if expires_raw:
                try:
                    expires = date.fromisoformat(str(expires_raw))
                    if expires < today:
                        continue  # drop expired
                except ValueError:
                    pass
            remaining.append(d)
        decisions_file.write_text(
            yaml.dump(remaining, default_flow_style=False, allow_unicode=True, sort_keys=False)
        )

    if not active:
        print(json.dumps({"additionalContext": ""}))
        return

    lines = [f"Remembered decisions ({len(active)}, last {lookback} days):"]
    for d, expires in active:
        text = d.get("text", "")
        if expires:
            days_left = (expires - today).days
            expiry_note = f"  [expires in {days_left}d]"
        else:
            expiry_note = ""
        lines.append(f"- {text}{expiry_note}")

    print(json.dumps({"additionalContext": "\n".join(lines)}))


if __name__ == "__main__":
    main()
