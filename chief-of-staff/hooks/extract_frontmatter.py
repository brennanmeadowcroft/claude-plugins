#!/usr/bin/env python3
"""
Extract frontmatter from all 01-Projects/*/PLAN.md files relative to cwd.
Outputs {"additionalContext": "<formatted project index>"} to stdout for Claude hook injection.
"""

import json
import sys
from datetime import date
from pathlib import Path


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown. Handles simple key: value pairs only."""
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in content[3:end].splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def format_deadline(due_date_str: str, today: date) -> str:
    try:
        due = date.fromisoformat(due_date_str)
        days = (due - today).days
        if days < 0:
            return f"due: {due_date_str} 🔴 overdue"
        elif days == 0:
            return f"due: {due_date_str} 🔴 today"
        elif days <= 7:
            return f"due: {due_date_str} ⚠️ {days}d"
        elif days <= 14:
            return f"due: {due_date_str} ⚠️ {days}d"
        else:
            return f"due: {due_date_str}"
    except ValueError:
        return f"due: {due_date_str}"


def main():
    projects_dir = Path("01-Projects")

    if not projects_dir.exists():
        print(json.dumps({"additionalContext": "No 01-Projects/ folder found in current directory."}))
        sys.exit(0)

    plan_files = sorted(projects_dir.glob("*/PLAN.md"))

    if not plan_files:
        print(json.dumps({"additionalContext": "01-Projects/ exists but contains no PLAN.md files."}))
        sys.exit(0)

    today = date.today()
    lines = [f"Project index ({len(plan_files)} project{'s' if len(plan_files) != 1 else ''}):"]

    for plan_file in plan_files:
        try:
            fm = parse_frontmatter(plan_file.read_text(encoding="utf-8"))
        except OSError:
            continue

        name = fm.get("name") or plan_file.parent.name
        description = fm.get("description", "").strip()
        due_date = fm.get("due_date", "").strip()
        area = fm.get("area", "").strip()

        meta = []
        if area:
            meta.append(f"area: {area}")
        if due_date:
            meta.append(format_deadline(due_date, today))
        else:
            meta.append("no deadline")

        lines.append(f"\n- **{name}** · {' · '.join(meta)}")
        if description:
            lines.append(f"  {description}")

    print(json.dumps({"additionalContext": "\n".join(lines)}))


if __name__ == "__main__":
    main()
