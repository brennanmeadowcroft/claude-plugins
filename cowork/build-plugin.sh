#!/usr/bin/env bash
# build-plugin.sh — packages the cowork plugin into a .plugin zip file
# Run from anywhere; the script resolves its own location.

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_NAME="$(python3 -c "import json; d=json.load(open('${PLUGIN_DIR}/.claude-plugin/plugin.json')); print(d['name'])")"
VERSION="$(python3 -c "import json; d=json.load(open('${PLUGIN_DIR}/.claude-plugin/plugin.json')); print(d['version'])")"
OUTPUT="${PLUGIN_DIR}/${PLUGIN_NAME}-${VERSION}.plugin"

echo "Building plugin: ${PLUGIN_NAME} v${VERSION}"
echo "Source:  ${PLUGIN_DIR}"
echo "Output:  ${OUTPUT}"
echo ""

# Remove any previous build (ignore failure — cp below will overwrite anyway)
rm -f "${OUTPUT}" || true

# Create the zip from inside the plugin directory so files sit at the root.
# Excludes:
#   - node_modules (installed at runtime via the SessionStart hook)
#   - macOS metadata files
#   - any previous .plugin builds
#   - git internals
(
  cd "${PLUGIN_DIR}"
  zip -r "/tmp/${PLUGIN_NAME}.plugin" . \
    --exclude "*/node_modules/*" \
    --exclude "*/.DS_Store" \
    --exclude "*.plugin" \
    --exclude "*/.git/*"
)

cp "/tmp/${PLUGIN_NAME}.plugin" "${OUTPUT}"
rm "/tmp/${PLUGIN_NAME}.plugin"

SIZE=$(du -sh "${OUTPUT}" | cut -f1)
echo "Done! ${OUTPUT} (${SIZE})"
