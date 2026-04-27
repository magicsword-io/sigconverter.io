#!/bin/sh

cd backend/ && ./launch-backends.sh && cd ..

# wait for at least one backend to be ready before starting the frontend
echo "Waiting for backends to start..."
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    # check if any backend port (8xxx) is listening
    if ls /app/backend/ | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
        for version_dir in /app/backend/[0-9]*/; do
            version=$(basename "$version_dir")
            port=$(echo "8${version}" | tr -d '.')
            if curl -s -o /dev/null -w '' "http://localhost:${port}/api/v1/targets" 2>/dev/null; then
                echo "Backend for sigma $version is ready on port $port"
                READY=1
                break
            fi
        done
        [ "${READY:-0}" -eq 1 ] && break
    fi
    sleep 1
    WAITED=$((WAITED + 1))
    echo "Still waiting... ($WAITED/$MAX_WAIT)"
done

if [ "${READY:-0}" -ne 1 ]; then
    echo "WARNING: No backends responded within ${MAX_WAIT}s. Starting frontend anyway."
    echo "Check backend logs above for errors."
fi

cd frontend && uv run frontend.py
