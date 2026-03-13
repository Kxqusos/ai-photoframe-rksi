# Docker Deploy

Docker assets are now split by role:
- `deploy/docker/`: image definitions
- `deploy/compose/`: dev and prod Compose entrypoints
- `deploy/env/`: example env files for backend and postgres
- `deploy/scripts/`: container startup helpers

## Validation
Validate the staged Compose files before bringing anything up:
```bash
docker compose -f deploy/compose/docker-compose.dev.yml config
docker compose -f deploy/compose/docker-compose.prod.yml config
```

## Env Files
Do not run production directly from the tracked `*.example` files. Create real env files first:
```bash
cp deploy/env/backend.env.example deploy/env/backend.env
cp deploy/env/postgres.env.example deploy/env/postgres.env
```

Then edit at least:
- `AUTH__JWT_SECRET`
- `AUTH__ADMIN_PASSWORD`
- `POSTGRES_PASSWORD`
- `OPENROUTER__API_KEY`

## Dev Stack
```bash
docker compose -f deploy/compose/docker-compose.dev.yml up --build
```

Dev services:
- `postgres`: PostgreSQL 17 with healthcheck and persistent volume
- `backend`: waits for PostgreSQL, runs Alembic migrations, bootstraps default room, then starts `uvicorn --reload`
- `frontend`: runs Vite dev server behind nginx
- `nginx`: public entrypoint for frontend and backend routes

The root `docker-compose.yml` forwards to the dev stack for convenience.

## Prod Stack
```bash
docker compose -f deploy/compose/docker-compose.prod.yml up --build -d
```

Prod compose keeps the same topology, removes source mounts and reload-mode settings, and serves the built frontend through a static file server inside the frontend container.

## SQLite Cutover
- Runtime and deployment are PostgreSQL-first.
- If you still have a legacy SQLite file, start PostgreSQL-backed schema first and then import data once:
  `cd backend && uv run python scripts/migrate_sqlite_to_postgres.py --source ./photoframe.db`
- Pytest may still use disposable SQLite files for isolated test runs. That is test harness behavior, not the runtime deployment model.
