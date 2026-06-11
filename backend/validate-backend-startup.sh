#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [ "$#" -gt 0 ]; then
    SIGMA_VERSIONS=$(printf '%s\n' "$@")
else
    SIGMA_VERSIONS=$(python3 "$SCRIPT_DIR/list_sigma_versions.py")
fi

if [ -z "$SIGMA_VERSIONS" ]; then
    echo "No pinned sigma version directories found under $SCRIPT_DIR" >&2
    exit 1
fi

validate_backend() {
    local version="$1"
    local port="8${version//./}"
    local log_file
    local pid
    local healthy=false
    local attempt=0

    log_file=$(mktemp)

    echo "Starting backend for sigma-cli ${version} on port ${port}"
    "$SCRIPT_DIR/$version/.venv/bin/python" "$SCRIPT_DIR/backend.py" >"$log_file" 2>&1 &
    pid=$!
    sleep 1

    while [ "$attempt" -lt 20 ]; do
        if curl -fsS "http://127.0.0.1:${port}/api/v1/targets" >/dev/null 2>&1; then
            healthy=true
            break
        fi

        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi

        attempt=$((attempt + 1))
        sleep 1
    done

    if [ "$healthy" != "true" ]; then
        echo "Backend startup failed for sigma-cli ${version}"
        cat "$log_file"
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
        rm -f "$log_file"
        return 1
    fi

    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    rm -f "$log_file"
    echo "OK ${version}"
}

while IFS= read -r VERSION; do
    validate_backend "$VERSION"
done <<EOF
$SIGMA_VERSIONS
EOF
