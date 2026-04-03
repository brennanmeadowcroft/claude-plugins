#!/usr/bin/env bash
# build-plugin.sh — packages the chief-of-staff plugin into a .plugin zip file
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

rm -f "${OUTPUT}" || true

(
  cd "${PLUGIN_DIR}"
  zip -r "/tmp/${PLUGIN_NAME}.plugin" . \
    --exclude "*/.DS_Store" \
    --exclude "*.plugin" \
    --exclude "*/.git/*"
)

cp "/tmp/${PLUGIN_NAME}.plugin" "${OUTPUT}"
rm "/tmp/${PLUGIN_NAME}.plugin"

SIZE=$(du -sh "${OUTPUT}" | cut -f1)
echo "Done! ${OUTPUT} (${SIZE})"
