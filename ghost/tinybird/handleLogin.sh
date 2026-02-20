#!/bin/bash
set -e

TINYB_FILE="/home/tinybird/.tinyb"

# Command mode: arguments passed (e.g. "get-tokens") — verify already logged in
if [ $# -gt 0 ]; then
    if [ ! -f "$TINYB_FILE" ]; then
        echo "Error: Not logged in to Tinybird." >&2
        echo "Run: docker compose run --rm tinybird-login" >&2
        exit 1
    fi
    exec "$@"
fi

# Login mode: no arguments
if [ -f "$TINYB_FILE" ]; then
    echo "Tinybird already logged in"
    exit 0
fi

# Require interactive terminal to avoid hanging in background runs
if [ ! -t 0 ] || [ ! -t 1 ]; then
    echo "Error: Tinybird login requires an interactive terminal." >&2
    echo "Run: docker compose run --rm tinybird-login" >&2
    exit 1
fi

tb login --method code
