#!/bin/sh
set -eu

attempts="${POSTGRES_READY_ATTEMPTS:-30}"
sleep_seconds="${POSTGRES_READY_SLEEP_SECONDS:-2}"
counter=1

while [ "$counter" -le "$attempts" ]; do
  if uv run python scripts/check_postgres_ready.py; then
    exit 0
  fi
  sleep "$sleep_seconds"
  counter=$((counter + 1))
done

exit 1
