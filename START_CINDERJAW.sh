#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
if [ "$#" -eq 0 ]; then
    exec python3 OPEN_CINDERJAW.py
fi
exec python3 cinderjaw_harvester.py "$@"
