#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

patch_legacy_sigma_install() {
    find ./.venv -iwholename "*sigma/conversion/base.py" -exec sed -i "/from pyparsing import Set/d" {} +
    find ./.venv -iwholename "*sigma/exceptions.py" -exec sed -i "/from pyparsing import List/d" {} +
}

mapfile -t SIGMA_VERSIONS < <(
    find "$SCRIPT_DIR" -mindepth 1 -maxdepth 1 -type d -regextype posix-extended \
        -regex '.*/[0-9]+\.[0-9]+\.[0-9]+' -printf '%f\n' | sort -V
)

if [ ${#SIGMA_VERSIONS[@]} -eq 0 ]; then
    echo "No pinned sigma version directories found under $SCRIPT_DIR" >&2
    echo "Run python3 ./backend/update_sigma_plugins.py once to generate them before building." >&2
    exit 1
fi

for VERSION in "${SIGMA_VERSIONS[@]}"; do
    VERSION_DIR="$SCRIPT_DIR/$VERSION"
    echo "Installing pinned backend environment for sigma-cli version: $VERSION"
    (
        cd "$VERSION_DIR"
        uv venv
        uv sync --frozen --no-dev
        patch_legacy_sigma_install
    )
done
