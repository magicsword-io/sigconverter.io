#!/bin/sh

cd backend/ && ./launch-backends.sh && cd ..
cd frontend && uv run frontend.py
