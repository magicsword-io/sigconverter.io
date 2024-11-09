#!/bin/bash

# Specify the directory to search in (or use the current directory)
directory="./"

# Iterate over all subdirectories
for dir in "$directory"/*/; do
    if [ -d "$dir" ]; then
        version=$(basename $dir)
        echo "Launching sigconverter backend for sigma version: $version"
        ./$version/.venv/bin/python ./backend.py &
    fi
done
