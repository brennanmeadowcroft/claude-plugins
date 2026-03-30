#!/usr/bin/env bash
# check-dependencies.sh
# Checks whether orientation-tools dependencies are installed.
# Always exits 0 — output is informational only, never blocks.

set -euo pipefail

MISSING_STACK=0
MISSING_UNIVERSAL=0

# ── Stack detection ────────────────────────────────────────────────────────────
TARGET="${1:-.}"
STACK="unknown"

if [[ -f "$TARGET/tsconfig.json" || -f "$TARGET/package.json" ]]; then
  # Prefer TypeScript if tsconfig exists alongside package.json
  if [[ -f "$TARGET/tsconfig.json" ]]; then
    STACK="typescript"
  else
    STACK="javascript"
  fi
elif [[ -f "$TARGET/go.mod" ]]; then
  STACK="go"
elif [[ -f "$TARGET/pyproject.toml" || -f "$TARGET/setup.py" || -f "$TARGET/requirements.txt" ]]; then
  STACK="python"
fi

echo "Checking orientation-tools dependencies..."
if [[ "$STACK" != "unknown" ]]; then
  echo "Detected stack: $STACK"
else
  echo "Stack: could not detect (no package.json/tsconfig.json/go.mod/pyproject.toml found)"
fi
echo ""

# ── Helper ─────────────────────────────────────────────────────────────────────
check_universal() {
  local name="$1"
  local cmd="$2"
  local hint="$3"
  if command -v "$cmd" &>/dev/null; then
    echo "  [✓] $name"
  else
    echo "  [✗] $name — $hint"
    MISSING_UNIVERSAL=$((MISSING_UNIVERSAL + 1))
  fi
}

check_stack() {
  local name="$1"
  local test_cmd="$2"
  local hint="$3"
  local applicable="$4"   # "yes" or "no"
  local stack_label="$5"  # e.g. "TypeScript/JS"

  if [[ "$applicable" == "yes" ]]; then
    if eval "$test_cmd" &>/dev/null 2>&1; then
      echo "  [✓] $name"
    else
      echo "  [✗] $name — $hint"
      MISSING_STACK=$((MISSING_STACK + 1))
    fi
  else
    # Not applicable — print informational only
    if eval "$test_cmd" &>/dev/null 2>&1; then
      echo "  [✓] $name (not detected in this project)"
    else
      echo "  [–] $name (not detected in this project) — $hint"
    fi
  fi
}

# ── Universal tools ────────────────────────────────────────────────────────────
echo "  Universal tools:"
check_universal "dot (graphviz)" "dot" "brew install graphviz"
check_universal "scc" "scc" "brew install scc"
echo ""

# ── TypeScript/JS tools ────────────────────────────────────────────────────────
ts_applicable="no"
[[ "$STACK" == "typescript" || "$STACK" == "javascript" ]] && ts_applicable="yes"
echo "  TypeScript/JS tools:"
check_stack \
  "dependency-cruiser (via npx)" \
  "npx --no dependency-cruiser --version" \
  "npm install -g dependency-cruiser  (or use via npx without installing)" \
  "$ts_applicable" \
  "TypeScript/JS"
echo ""

# ── Python tools ──────────────────────────────────────────────────────────────
py_applicable="no"
[[ "$STACK" == "python" ]] && py_applicable="yes"
echo "  Python tools:"
check_stack \
  "pyreverse" \
  "command -v pyreverse" \
  "pip install pylint  (pyreverse is bundled with pylint)" \
  "$py_applicable" \
  "Python"
echo ""

# ── Go tools ──────────────────────────────────────────────────────────────────
go_applicable="no"
[[ "$STACK" == "go" ]] && go_applicable="yes"
echo "  Go tools:"
check_stack \
  "goda" \
  "command -v goda" \
  "go install github.com/loov/goda@latest" \
  "$go_applicable" \
  "Go"
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
if [[ $MISSING_UNIVERSAL -eq 0 && $MISSING_STACK -eq 0 ]]; then
  echo "All tools for your stack are installed."
else
  msgs=()
  [[ $MISSING_UNIVERSAL -gt 0 ]] && msgs+=("$MISSING_UNIVERSAL universal tool(s) missing")
  [[ $MISSING_STACK -gt 0 ]] && msgs+=("$MISSING_STACK stack tool(s) missing")
  joined=$(IFS=", "; echo "${msgs[*]}")
  echo "$joined. Install missing tools for full functionality."
fi

exit 0
