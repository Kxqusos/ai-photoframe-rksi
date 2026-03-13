#!/bin/sh
set -eu

cd /app/backend

/usr/local/bin/wait-for-postgres.sh
uv run python scripts/run_migrations.py
uv run python scripts/bootstrap_default_room.py

set -- uv run uvicorn photoframe_backend.main:app --host 0.0.0.0 --port "${BACKEND_PORT:-8000}"
if [ "${BACKEND_RELOAD:-false}" = "true" ]; then
  set -- "$@" --reload
fi

exec "$@"
