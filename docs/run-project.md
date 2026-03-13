# Project Run Guide

## Requirements
- Python 3.14+
- Node.js 20+
- `uv`

## 1) Backend
```bash
cd backend
cp .env.example .env
```

Set at least these variables in `backend/.env`:
- `OPENROUTER__API_KEY`
- `AUTH__JWT_SECRET`
- `AUTH__ADMIN_USERNAME`
- `AUTH__ADMIN_PASSWORD`
- `APP__DEFAULT_PUBLIC_ROOM_SLUG` (8-char slug `[a-z0-9]`, default `ph000000`)
- `DB__HOST`, `DB__PORT`, `DB__NAME`, `DB__USER`, `DB__PASSWORD`

Bootstrap backend and run API:
```bash
cd backend
uv run python scripts/check_postgres_ready.py
uv run python scripts/run_migrations.py
uv run python scripts/bootstrap_default_room.py
uv run uvicorn photoframe_backend.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

## 2) Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

## 3) Quick Smoke Check
1. Open `http://127.0.0.1:5173/admin/login` and sign in.
2. Create room(s) in `/admin`.
3. Open `/{room_slug}` (for example `/ph000000`) and run generation.
4. Verify gallery isolation at `/{room_slug}/gallery`.

## Notes
- Legacy wrappers (`/api/prompts`, `/api/jobs/*`) still map to default room.
- Runtime and deploy are PostgreSQL-first. Use `uv run python scripts/migrate_sqlite_to_postgres.py --source ./photoframe.db` only for one-off legacy data import.
- For full details, see `docs/run-local.md`.
