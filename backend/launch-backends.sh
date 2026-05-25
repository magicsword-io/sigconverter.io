#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

mapfile -t SIGMA_VERSIONS < <(
    find "$SCRIPT_DIR" -mindepth 1 -maxdepth 1 -type d -regextype posix-extended \
        -regex '.*/[0-9]+\.[0-9]+\.[0-9]+' -printf '%f\n' | sort -V
)

for VERSION in "${SIGMA_VERSIONS[@]}"; do
    echo "Launching sigconverter backend for sigma version: $VERSION"
    "$SCRIPT_DIR/$VERSION/.venv/bin/python" "$SCRIPT_DIR/backend.py" &
done
