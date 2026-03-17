# Docker Deploy

The project now uses a single standalone root `docker-compose.yml`.

Supporting assets remain split by role:
- `deploy/docker/`: image definitions
- `deploy/env/`: example env files for backend and postgres
- `deploy/scripts/`: container startup helpers

## Validation
Validate the root Compose file before bringing anything up:
```bash
docker compose config
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

Recommended minimums before first deploy:
- Set `AUTH__JWT_SECRET` to a random secret with at least 32 bytes.
- Set `AUTH__ADMIN_PASSWORD` and `POSTGRES_PASSWORD` to non-default values.
- If you use direct `openai_compatible`, also fill `OPENAI_COMPATIBLE__BASE_URL` and `OPENAI_COMPATIBLE__API_KEY`.

## LLM Routing via VLESS+Reality
The stack now includes:
- `xray-client`: client-side Xray container that applies a `vless://...` Reality link
- `llm-egress`: internal proxy used only for LLM provider traffic

You do not need to prefill the VLESS link in env files for the first startup.
Recommended flow:
1. Start the stack once.
2. Open `/admin/login`.
3. Go to the `LLM Routing` card in admin dashboard.
4. Paste the full `vless://...` URI.
5. Click `Сохранить и применить`.
6. Click `Проверить подключение`.
7. When status becomes `active`, click `Включить маршрутизацию`.

If you want to preconfigure internal service URLs explicitly, keep these values:
```env
ROUTING_LLM_EGRESS_URL=http://llm-egress:8080
ROUTING_XRAY_CLIENT_URL=http://xray-client:8081
```

## Start Stack
```bash
docker compose up -d --build
```

Services:
- `postgres`: PostgreSQL 17 with healthcheck and persistent volume
- `backend`: waits for PostgreSQL, runs Alembic migrations, bootstraps default room, then starts a single `uvicorn` process
- `xray-client`: applies VLESS+Reality client config and exposes local proxy ports for routed traffic
- `llm-egress`: forwards current LLM requests through `xray-client`
- `frontend`: runs Vite dev server behind nginx
- `nginx`: public entrypoint for frontend and backend routes

After the first deploy, useful checks:
```bash
docker compose ps
docker compose logs backend --tail=100
docker compose logs llm-egress --tail=100
docker compose logs xray-client --tail=100
```

## SQLite Cutover
- Runtime and deployment are PostgreSQL-first.
- If you still have a legacy SQLite file, start PostgreSQL-backed schema first and then import data once:
  `cd backend && uv run python scripts/migrate_sqlite_to_postgres.py --source ./photoframe.db`
- Pytest may still use disposable SQLite files for isolated test runs. That is test harness behavior, not the runtime deployment model.
