#!/usr/bin/env python3
"""Initialize ChromaDB vector store for meeting memory.

Creates the .meeting-memory/ store at the vault root and adds a .gitignore entry
so Nextcloud does not sync it.
"""

import importlib
import os
import site
import subprocess
import sys


def find_vault_root():
    """Walk up from CWD to find the directory containing .claude/."""
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()


def check_python():
    print("Checking python3.13...", end=" ")
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True, text=True, check=True
        )
        print(f"OK ({result.stdout.strip()})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FAILED")
        print("Error: python3.13 is required. Install it via: brew install python@3.13")
        return False


def install_chromadb():
    print("Checking chromadb...", end=" ")
    try:
        import chromadb  # noqa: F401
        print("OK (already installed)")
        return True
    except ImportError:
        pass

    print("not found, installing...")
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
        print("  chromadb installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  FAILED to install chromadb: {e.stderr}")
        return False


def setup_gitignore(vault_root):
    """Ensure .meeting-memory/ is in .gitignore at the vault root."""
    gitignore_path = os.path.join(vault_root, ".gitignore")
    entry = ".meeting-memory/"
    print(f"Checking .gitignore for '{entry}'...", end=" ")

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.read()
        if entry in content.splitlines():
            print("OK (already present)")
            return True
        with open(gitignore_path, "a") as f:
            if not content.endswith("\n"):
                f.write("\n")
            f.write(f"{entry}\n")
        print("OK (appended)")
    else:
        with open(gitignore_path, "w") as f:
            f.write(f"{entry}\n")
        print("OK (created)")
    return True


def fix_db_permissions(db_path):
    for dirpath, _, filenames in os.walk(db_path):
        os.chmod(dirpath, 0o755)
        for filename in filenames:
            os.chmod(os.path.join(dirpath, filename), 0o644)


def smoke_test(vault_root):
    """Create the ChromaDB store and meetings collection."""
    print("Initializing ChromaDB...", end=" ")
    db_path = os.path.join(vault_root, ".meeting-memory")

    try:
        import chromadb
        os.makedirs(db_path, mode=0o755, exist_ok=True)
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(
            name="meetings",
            metadata={"hnsw:space": "cosine"}
        )
        count = collection.count()
        fix_db_permissions(db_path)
        print(f"OK (collection 'meetings' has {count} documents)")
        print(f"  Database path: {db_path}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def main():
    print("=" * 50)
    print("Meeting Memory Initialization")
    print("=" * 50)
    print()

    vault_root = find_vault_root()
    print(f"Vault root: {vault_root}")
    print()

    steps = [
        ("Python check", lambda: check_python()),
        ("Install chromadb", lambda: install_chromadb()),
        ("Setup .gitignore", lambda: setup_gitignore(vault_root)),
        ("Smoke test", lambda: smoke_test(vault_root)),
    ]

    for name, fn in steps:
        if not fn():
            print(f"\nSetup failed at: {name}")
            sys.exit(1)
        print()

    print("=" * 50)
    print("Meeting memory initialized successfully!")
    print()
    print("Next steps:")
    print("  - Run /process-transcripts to index meeting notes automatically")
    print("  - Run /ask-meetings <question> to query your meeting history")
    print("=" * 50)


if __name__ == "__main__":
    main()
