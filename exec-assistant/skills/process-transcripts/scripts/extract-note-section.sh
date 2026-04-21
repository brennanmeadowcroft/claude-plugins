#!/bin/bash
# extract-note-section.sh
# Extracts a single date section (## YYYY-MM-DD) from an Obsidian meeting note.
#
# Usage:   extract-note-section.sh <note-file> <date>
# Example: extract-note-section.sh "/path/to/Craig Swank - 2026.md" "2026-04-14"
#
# Prints from the matching ## YYYY-MM-DD heading up to (but not including)
# the next ## YYYY-MM-DD heading. Exits with status 1 if the section is not found.

NOTE_FILE="$1"
DATE="$2"

if [ -z "$NOTE_FILE" ] || [ -z "$DATE" ]; then
  echo "Usage: $0 <note-file> <date (YYYY-MM-DD)>" >&2
  exit 1
fi

if [ ! -f "$NOTE_FILE" ]; then
  echo "Error: File not found: $NOTE_FILE" >&2
  exit 1
fi

output=$(awk -v target="## ${DATE}" '
  found && /^## [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/ { exit }
  $0 == target { found=1 }
  found { print }
' "$NOTE_FILE")

if [ -z "$output" ]; then
  echo "Error: No section found for date ${DATE} in ${NOTE_FILE}" >&2
  exit 1
fi

echo "$output"
