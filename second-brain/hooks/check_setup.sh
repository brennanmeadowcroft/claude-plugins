#!/usr/bin/env bash
# Check that the thinking-partner plugin prerequisites are in place.
# Runs on every UserPromptSubmit — must stay fast (no network calls).

ERRORS=()

if ! command -v op &>/dev/null; then
  ERRORS+=("1Password CLI (op) not found in PATH. Install from: https://developer.1password.com/docs/cli/get-started/")
fi

ENV_FILE="${HOME}/.config/karakeep.env"
if [[ ! -f "$ENV_FILE" ]]; then
  ERRORS+=("Missing ${ENV_FILE}. See the thinking-partner README for setup instructions.")
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
  echo "thinking-partner: setup incomplete" >&2
  for err in "${ERRORS[@]}"; do
    echo "  • $err" >&2
  done
  exit 1
fi
