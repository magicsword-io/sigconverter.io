#!/bin/bash

# Specify the directory to search in
directory="./"

# Iterate over all subdirectories
for dir in "$directory"/*/; do
    if [ -d "$dir" ]; then
        version=$(basename $dir)
        echo "Launching sigconverter backend for sigma version: $version"
        # Add timeout to ensure previous instance has time to start
        sleep 2
        ./$version/.venv/bin/python ./backend.py &
        
        # Check if launch was successful
        if [ $? -ne 0 ]; then
            echo "Failed to launch backend for version $version"
        fi
    fi
done

# Wait for all backends to be ready
sleep 5