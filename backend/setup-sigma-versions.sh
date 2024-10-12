#!/bin/bash

# fetch 10 latest versions of sigma-cli
SIGMA_VERSIONS=$(curl -s https://pypi.org/pypi/sigma-cli/json | jq -r '.releases | keys | .[-10:] | .[]')

# prepare virtualenv for each version
for VERSION in $SIGMA_VERSIONS; do
    # prepare folder to contain a single version
    mkdir $VERSION
    cp pyproject.toml uv.lock $VERSION
    cd $VERSION
    uv venv && uv -q pip sync pyproject.toml

    # fetch all plugins from plugin directory json and install latest compatible plugins available
    uv -q add sigma-cli==$VERSION
    curl https://raw.githubusercontent.com/SigmaHQ/pySigma-plugin-directory/refs/heads/main/pySigma-plugins-v1.json | jq '.plugins[].package' | xargs -n 1 uv add -q

    # remove if installed because of https://github.com/redsand/pySigma-backend-hawk/issues/1
    uv -q remove pySigma-backend-hawk
    uv -q remove pysigma-backend-kusto
    cd ..
done
