# Run Local

## Requirements
- Python 3.14+
- Node.js 20+
- `uv`

## Backend
1. `cd backend`
2. `cp .env.example .env` and fill values
   - Local runtime is PostgreSQL-first. Point `DB__HOST`, `DB__PORT`, `DB__NAME`, `DB__USER`, and `DB__PASSWORD` at a running PostgreSQL instance.
   - Grouped env format is now required: `APP__*`, `AUTH__*`, `DB__*`, `LOG__*`, `OPENROUTER__*`, `STORAGE__*`.
   - `DATABASE_URL` is a legacy compatibility override only. New local and deploy setup should use grouped `DB__*` values.
   - For faster generation routing: keep `OPENROUTER__PROVIDER_SORT=throughput` and tune `OPENROUTER__PREFERRED_MAX_LATENCY` (seconds).
   - Source image is preprocessed before OpenRouter call (`OPENROUTER__SOURCE_MAX_SIDE`, `OPENROUTER__SOURCE_JPEG_QUALITY`).
   - If OpenRouter returns a response without image data, backend retries automatically (`OPENROUTER__MISSING_IMAGE_RETRIES`).
   - Generated output is JPEG by default (`OPENROUTER__RESULT_FORMAT=jpeg`, quality via `OPENROUTER__JPEG_QUALITY`).
   - Generated files are stored for `STORAGE__RESULT_RETENTION_DAYS` and then pruned.
   - Backend writes logs to `backend/logs/backend.log` by default (`LOG__FILE_PATH`).
   - JWT/admin setup:
     - `AUTH__JWT_SECRET` must be non-default in non-test environments.
     - `AUTH__ADMIN_USERNAME` and `AUTH__ADMIN_PASSWORD` configure single admin account.
     - `APP__DEFAULT_PUBLIC_ROOM_SLUG` controls which room legacy wrappers (`/api/jobs`, `/api/prompts`) point to.
3. `uv run python scripts/check_postgres_ready.py`
4. `uv run python scripts/run_migrations.py`
5. `uv run python scripts/bootstrap_default_room.py`
6. If you have a legacy SQLite database, migrate it once:
   - `uv run python scripts/migrate_sqlite_to_postgres.py --source ./photoframe.db`
7. `uv run uvicorn photoframe_backend.main:app --reload`

Backend starts at `http://127.0.0.1:8000`.

## Frontend
1. `cd frontend`
2. `cp .env.example .env` (optional)
3. `npm install`
4. `npm run dev`

Frontend starts at `http://127.0.0.1:5173`.

## End-to-end check
1. Open `/admin/login`, sign in with `AUTH__ADMIN_USERNAME` and `AUTH__ADMIN_PASSWORD`.
2. In `/admin`, create two rooms with different models and short slugs (`8` chars `[a-z0-9]`), for example `aaaaaaaa`, `bbbbbbbb`.
3. In each room editor, create prompts and upload preview/icon media.
4. Open `/ph000000` (or another room slug), upload a photo, and generate an image.
5. Open `/ph000000/gallery` and verify only that room's results are shown.
6. Resolve status via `GET /api/rooms/ph000000/jobs/hash/{jpg_hash}` and confirm room scoping.
7. Verify `/qr/{qr_hash}` downloads generated file.

## Tests
- Pytest uses a disposable per-run SQLite file for isolation only.
- Runtime configuration and deploy docs remain PostgreSQL-first.
- If you want real PostgreSQL integration coverage, set `TEST_DATABASE_URL` explicitly for those tests.
