#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SIGMA_VERSIONS=$(python3 "$SCRIPT_DIR/list_sigma_versions.py")

if [ -z "$SIGMA_VERSIONS" ]; then
    echo "No pinned sigma version directories found under $SCRIPT_DIR" >&2
    exit 1
fi

while IFS= read -r VERSION; do
    echo "Launching sigconverter backend for sigma version: $VERSION"
    "$SCRIPT_DIR/$VERSION/.venv/bin/python" "$SCRIPT_DIR/backend.py" &
done <<EOF
$SIGMA_VERSIONS
EOF
