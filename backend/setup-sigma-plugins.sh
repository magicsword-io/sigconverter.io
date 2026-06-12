#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SIGMA_VERSIONS=$(python3 "$SCRIPT_DIR/list_sigma_versions.py")

if [ -z "$SIGMA_VERSIONS" ]; then
    echo "No pinned sigma version directories found under $SCRIPT_DIR" >&2
    echo "Run python3 ./backend/update_sigma_plugins.py once to generate them before building." >&2
    exit 1
fi

while IFS= read -r VERSION; do
    VERSION_DIR="$SCRIPT_DIR/$VERSION"
    echo "Installing pinned backend environment for sigma-cli version: $VERSION"
    (
        cd "$VERSION_DIR"
        uv venv
        uv sync --frozen --no-dev
    )
done <<EOF
$SIGMA_VERSIONS
EOF
