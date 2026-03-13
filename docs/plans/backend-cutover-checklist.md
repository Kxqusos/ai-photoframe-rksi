# Backend Cutover Checklist

1. Back up the legacy SQLite file before any migration step.
2. Prepare PostgreSQL runtime env:
   - `cp deploy/env/backend.env.example deploy/env/backend.env`
   - `cp deploy/env/postgres.env.example deploy/env/postgres.env`
   - replace placeholder secrets and passwords
3. Validate deploy config:
   - `docker compose -f deploy/compose/docker-compose.dev.yml config`
   - `docker compose -f deploy/compose/docker-compose.prod.yml config`
4. Apply schema to PostgreSQL:
   - `cd backend && uv run python scripts/check_postgres_ready.py`
   - `cd backend && uv run python scripts/run_migrations.py`
5. If legacy data exists, import it once:
   - `cd backend && uv run python scripts/migrate_sqlite_to_postgres.py --source /absolute/path/to/photoframe.db`
6. Bootstrap the default room:
   - `cd backend && uv run python scripts/bootstrap_default_room.py`
7. Start backend from the src entrypoint:
   - `cd backend && uv run uvicorn photoframe_backend.main:app --reload`
8. Verify:
   - `GET /api/health`
   - admin login at `/api/admin/auth/login`
   - room-scoped prompt listing and job creation
   - gallery and `/qr/{qr_hash}` download flow
9. Switch deploy envs and traffic only after the PostgreSQL-backed checks above are green.
