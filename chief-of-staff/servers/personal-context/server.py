#!/usr/bin/env python3
"""Personal context MCP server for chief-of-staff skills.

Reads from ~/.config/chief-of-staff/:
  contacts.yaml     — structured people directory (name, email, aliases)
  *.md files        — personal context files (communication-style.md, role.md, etc.)

Re-reads files on every call so edits take effect without restarting the server.
"""

import yaml
from pathlib import Path
from mcp.server.fastmcp import FastMCP

CONFIG_DIR = Path.home() / ".claude-personal" / "context"

mcp = FastMCP("personal-context")


def _load_contacts() -> list[dict]:
    contacts_file = CONFIG_DIR / "contacts.yaml"
    if not contacts_file.exists():
        raise FileNotFoundError(
            f"contacts.yaml not found at {contacts_file}. "
            "Create it at ~/.claude-personal/context/contacts.yaml — see the chief-of-staff README for the expected format."
        )
    with contacts_file.open() as f:
        data = yaml.safe_load(f) or {}
    return data.get("people", [])


def _find_md_files() -> dict[str, Path]:
    if not CONFIG_DIR.exists():
        return {}
    return {p.stem: p for p in sorted(CONFIG_DIR.glob("*.md"))}


@mcp.tool()
def lookup_contact(email: str) -> dict | None:
    """Look up a contact by email address.

    Args:
        email: The email address to search for (case-insensitive).

    Returns:
        The contact object (name, email, aliases, team, notes) or null if not found.
    """
    email_lower = email.lower().strip()
    for person in _load_contacts():
        if person.get("email", "").lower() == email_lower:
            return person
    return None


@mcp.tool()
def find_contact(query: str) -> dict | None:
    """Find a contact by name, alias, or partial name.

    Searches in order: exact name match → alias match → partial name match (all case-insensitive).
    Returns the first match found.

    Args:
        query: A full name, first name, alias, or partial name to search for.

    Returns:
        The contact object (name, email, aliases, team, notes) or null if not found.
    """
    query_lower = query.lower().strip()
    contacts = _load_contacts()

    # 1. Exact full name match
    for person in contacts:
        if person.get("name", "").lower() == query_lower:
            return person

    # 2. Alias match
    for person in contacts:
        aliases = [a.lower() for a in person.get("aliases", [])]
        if query_lower in aliases:
            return person

    # 3. Partial name match (query is contained in name)
    for person in contacts:
        if query_lower in person.get("name", "").lower():
            return person

    return None


@mcp.tool()
def list_contacts() -> list[dict]:
    """Return all contacts from contacts.yaml.

    Returns:
        List of all contact objects.
    """
    return _load_contacts()


@mcp.tool()
def get_context_file(topic: str) -> str | None:
    """Read a personal context markdown file by topic name.

    Topic names correspond to filenames without the .md extension.
    For example, topic "communication-style" reads "communication-style.md".

    Args:
        topic: The topic name (e.g. "communication-style", "role-and-responsibilities").

    Returns:
        The full markdown content of the file, or null if not found.
    """
    path = _find_md_files().get(topic)
    if path is None:
        return None
    return path.read_text()


@mcp.tool()
def list_context_files() -> list[str]:
    """Return the names of all available personal context markdown files.

    Returns:
        Sorted list of topic names (filenames without .md extension).
    """
    return sorted(_find_md_files().keys())


if __name__ == "__main__":
    mcp.run()
