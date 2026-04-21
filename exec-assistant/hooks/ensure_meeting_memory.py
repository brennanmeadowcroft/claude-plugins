#!/usr/bin/env python3
"""Ensure the ChromaDB meeting memory store is initialized and healthy.

Runs on every UserPromptSubmit when Claude is working in the Obsidian vault.
Fast path (~<1s) when the store is already healthy. Initializes the store if
missing. Vault detection: only runs if 02-AreasOfResponsibility/ exists in CWD.
Exits non-zero on failure so Claude Code surfaces the error.
"""

import os
import sys


def find_vault_root():
    """Walk up from CWD to find the directory containing .claude/."""
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()


def is_vault(vault_root):
    """Return True only if this looks like the Obsidian vault."""
    return os.path.isdir(os.path.join(vault_root, "02-AreasOfResponsibility"))


def ensure_chromadb():
    """Import chromadb, installing it if missing."""
    try:
        import chromadb
        return chromadb
    except ImportError:
        pass

    import site
    import importlib
    import subprocess

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user",
             "--break-system-packages", "chromadb"],
            check=True, capture_output=True, text=True
        )
        user_site = site.getusersitepackages()
        if user_site not in sys.path:
            sys.path.insert(0, user_site)
        importlib.invalidate_caches()
        import chromadb
        return chromadb
    except Exception as e:
        print(f"Failed to install chromadb: {e}", file=sys.stderr)
        return None


def fix_db_permissions(db_path):
    for dirpath, _, filenames in os.walk(db_path):
        os.chmod(dirpath, 0o755)
        for filename in filenames:
            os.chmod(os.path.join(dirpath, filename), 0o644)


def main():
    vault_root = find_vault_root()

    # Only run in the Obsidian vault, not in coding project directories
    if not is_vault(vault_root):
        sys.exit(0)

    db_path = os.path.join(vault_root, ".meeting-memory")

    chromadb = ensure_chromadb()
    if chromadb is None:
        sys.exit(1)

    needs_init = not os.path.isdir(db_path)

    try:
        os.makedirs(db_path, mode=0o755, exist_ok=True)
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(
            name="meetings",
            metadata={"hnsw:space": "cosine"}
        )
        count = collection.count()
        fix_db_permissions(db_path)
    except Exception as e:
        print(f"Meeting memory error at {db_path}: {e}", file=sys.stderr)
        print("Run /init-meeting-memory to rebuild the store.", file=sys.stderr)
        sys.exit(1)

    if needs_init:
        print(f"Meeting memory initialized at {db_path}")
    else:
        print(f"Meeting memory ready ({count} documents) at {db_path}")


if __name__ == "__main__":
    main()
