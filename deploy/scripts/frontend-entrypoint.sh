#!/bin/sh
set -eu

cd /app/frontend

mode="${FRONTEND_MODE:-preview}"
host="${FRONTEND_HOST:-0.0.0.0}"
port="${FRONTEND_PORT:-4173}"

if [ ! -d node_modules ] || [ -z "$(ls -A node_modules 2>/dev/null)" ]; then
  npm ci
fi

if [ "$mode" = "dev" ]; then
  exec npm run dev -- --host "$host" --port "$port"
fi

npm run build
if [ "$mode" = "preview" ]; then
  exec npm run preview -- --host "$host" --port "$port"
fi

exec serve -s dist -l "$port"
