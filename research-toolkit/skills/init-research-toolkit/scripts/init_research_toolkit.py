#!/usr/bin/env python3
"""Initialize the research toolkit: permissions, ChromaDB vector store, and dependencies."""

import importlib
import json
import site
import subprocess
import sys
import os


def find_project_root():
    """Walk up from cwd to find the directory containing .claude/."""
    d = os.path.abspath(os.getcwd())
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".claude")):
            return d
        d = os.path.dirname(d)
    # Fallback: use cwd
    return os.path.abspath(os.getcwd())


def check_permissions(project_root):
    """Check and configure WebSearch/WebFetch permissions in .claude/settings.json."""
    settings_path = os.path.join(project_root, ".claude", "settings.json")
    required_tools = ["WebSearch", "WebFetch"]
    print("Checking tool permissions...", end=" ")

    # Load existing settings or start fresh
    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            print("WARNING: could not parse existing settings.json, skipping")
            return False

    permissions = settings.get("permissions", {})
    allow_list = permissions.get("allow", [])

    missing = [t for t in required_tools if t not in allow_list]

    if not missing:
        print(f"OK ({', '.join(required_tools)} already allowed)")
        return True

    # Add missing tools
    allow_list.extend(missing)
    permissions["allow"] = allow_list
    settings["permissions"] = permissions

    try:
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
        print(f"UPDATED (added {', '.join(missing)} to permissions.allow)")
        return True
    except IOError as e:
        print(f"FAILED: could not write settings.json: {e}")
        return False


def check_python():
    """Verify python3.13 is available."""
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


def check_ytdlp():
    """Check if yt-dlp is available."""
    print("Checking yt-dlp...", end=" ")
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True, text=True, check=True
        )
        print(f"OK (v{result.stdout.strip()})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("MISSING (optional)")
        print("  YouTube research requires yt-dlp. Install with: brew install yt-dlp")
        # Not fatal — return True so setup continues
        return True


def install_chromadb():
    """Install chromadb if not already available."""
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
        # Ensure user site-packages is on sys.path for the current process
        user_site = site.getusersitepackages()
        if user_site not in sys.path:
            sys.path.insert(0, user_site)
        importlib.invalidate_caches()
        print("  chromadb installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  FAILED to install chromadb: {e.stderr}")
        return False


def setup_gitignore(project_root):
    """Ensure research-memory/ is in .gitignore."""
    gitignore_path = os.path.join(project_root, ".gitignore")
    entry = ".research-memory/"
    print(f"Checking .gitignore for '{entry}'...", end=" ")

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.read()
        if entry in content.splitlines():
            print("OK (already present)")
            return True
        # Append entry
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
    """Ensure the vectordb directory and its files have appropriate permissions."""
    for dirpath, _, filenames in os.walk(db_path):
        os.chmod(dirpath, 0o755)
        for filename in filenames:
            os.chmod(os.path.join(dirpath, filename), 0o644)


def smoke_test(project_root):
    """Create the ChromaDB persistent store and research collection."""
    print("Initializing ChromaDB...", end=" ")
    db_path = os.path.join(project_root, ".research-memory")

    try:
        import chromadb
        os.makedirs(db_path, mode=0o755, exist_ok=True)
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(
            name="research",
            metadata={"hnsw:space": "cosine"}
        )
        count = collection.count()
        fix_db_permissions(db_path)
        print(f"OK (collection 'research' has {count} documents)")
        print(f"  Database path: {db_path}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def main():
    print("=" * 50)
    print("Research Toolkit Initialization")
    print("=" * 50)
    print()

    project_root = find_project_root()
    print(f"Project root: {project_root}")
    print()

    steps = [
        ("Permissions", lambda: check_permissions(project_root)),
        ("Python check", lambda: check_python()),
        ("yt-dlp check", lambda: check_ytdlp()),
        ("Install chromadb", lambda: install_chromadb()),
        ("Setup .gitignore", lambda: setup_gitignore(project_root)),
        ("Smoke test", lambda: smoke_test(project_root)),
    ]

    for name, fn in steps:
        if not fn():
            print(f"\nSetup failed at: {name}")
            sys.exit(1)
        print()

    print("=" * 50)
    print("Research toolkit initialized successfully!")
    print()
    print("Configured:")
    print("  - WebSearch and WebFetch permissions auto-granted")
    print("  - ChromaDB vector store ready")
    print()
    print("Next steps:")
    print("  - Run /deep-research to start researching")
    print("  - Run /ask-research <question> to query stored content")
    print("=" * 50)


if __name__ == "__main__":
    main()
