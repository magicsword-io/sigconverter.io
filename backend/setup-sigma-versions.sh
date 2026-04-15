#!/bin/bash

# fetch 10 latest versions of sigma-cli
SIGMA_VERSIONS=$(curl -s https://pypi.org/pypi/sigma-cli/json | jq -r '.releases | keys | map(select(contains("rc") | not)) | .[-10:] | .[]')

# prepare virtualenv for each version
for VERSION in $SIGMA_VERSIONS; do
    # prepare folder to contain a single version
    mkdir $VERSION
    cp pyproject.toml uv.lock $VERSION
    cd $VERSION
    uv venv && uv -q pip sync pyproject.toml

    # install sigma-cli and selected backends
    uv -q add sigma-cli==$VERSION
    uv -q add pysigma-backend-splunk
    uv -q add pySigma-backend-kusto

    # remove unused pyparsing imports in older version, see https://github.com/SigmaHQ/pySigma/pull/289#issuecomment-2410153076
    find ./ -iwholename "*sigma/conversion/base.py" -exec sed -i "/from pyparsing import Set/d" {} +
    find ./ -iwholename "*sigma/exceptions.py" -exec sed -i "/from pyparsing import List/d" {} +
    cd ..
done
