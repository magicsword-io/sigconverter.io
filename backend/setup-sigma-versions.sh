#!/bin/bash

# fetch 10 latest versions of sigma-cli
SIGMA_VERSIONS=$(curl -s https://pypi.org/pypi/sigma-cli/json | jq -r '.releases | keys | map(select(contains("rc") | not)) | .[-10:] | .[]')

# optional: a backends.txt file (one package per line, '#' comments allowed)
# selects which pySigma backends to install. If absent or empty, fall back to
# installing the full SigmaHQ plugin directory. The script runs from backend/,
# so the default lives at the repo root.
BACKENDS_FILE="${BACKENDS_FILE:-../backends.txt}"

# read user-selected backends, stripping comments and blank lines
SELECTED_BACKENDS=()
if [ -f "$BACKENDS_FILE" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        pkg="${line%%#*}"
        pkg="$(echo "$pkg" | xargs)"
        [ -n "$pkg" ] && SELECTED_BACKENDS+=("$pkg")
    done < "$BACKENDS_FILE"
fi

if [ "${#SELECTED_BACKENDS[@]}" -gt 0 ]; then
    echo "Installing ${#SELECTED_BACKENDS[@]} backend(s) from $BACKENDS_FILE"
else
    echo "No backends file found at $BACKENDS_FILE, using full SigmaHQ plugin directory"
fi

# prepare virtualenv for each version
for VERSION in $SIGMA_VERSIONS; do
    # prepare folder to contain a single version
    mkdir $VERSION
    cp pyproject.toml uv.lock $VERSION
    cd $VERSION
    uv venv && uv -q pip sync pyproject.toml

    uv -q add sigma-cli==$VERSION

    if [ "${#SELECTED_BACKENDS[@]}" -gt 0 ]; then
        # install only the user-selected backends
        for pkg in "${SELECTED_BACKENDS[@]}"; do
            uv -q add "$pkg"
        done
    else
        # fetch all plugins from plugin directory json and install latest compatible plugins available
        curl https://raw.githubusercontent.com/SigmaHQ/pySigma-plugin-directory/refs/heads/main/pySigma-plugins-v1.json | jq '.plugins[].package' | xargs -n 1 uv add -q

        # remove if installed because of https://github.com/redsand/pySigma-backend-hawk/issues/1
        uv -q remove pySigma-backend-hawk

        # some problems with kusto backend, disable for older sigma versions
        if [[ $VERSION == 0.* ]]; then
            uv -q remove pySigma-backend-kusto
        fi

        if [[ $VERSION == 2.* ]]; then
            uv -q remove pySigma-backend-cortexxdr
            uv -q remove pySigma-backend-opensearch
            uv -q remove pysigma-backend-carbonblack
        fi
    fi

    if [[ $VERSION == 3.* ]]; then
        uv -q remove pySigma-backend-cortexxdr
        uv -q remove pySigma-backend-opensearch
        uv -q remove pysigma-backend-carbonblack
    fi

    # remove unused pyparsing imports in older version, see https://github.com/SigmaHQ/pySigma/pull/289#issuecomment-2410153076
    find ./ -iwholename "*sigma/conversion/base.py" -exec sed -i "/from pyparsing import Set/d" {} +
    find ./ -iwholename "*sigma/exceptions.py" -exec sed -i "/from pyparsing import List/d" {} +
    cd ..
done
