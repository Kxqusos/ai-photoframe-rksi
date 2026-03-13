# Repository Guidelines

## Project Structure & Module Organization
- `frontend/` contains the React + TypeScript UI; primary code is in `frontend/src/`, with colocated `*.test.ts(x)` files.
- `backend/` is in transition. New backend work should target `backend/src/photoframe_backend/` with layered packages:
  - `api/http`
  - `application/services`
  - `domain/{entities,repositories}`
  - `infrastructure/{db,settings,clients,storage}`
  - `shared`
- `backend/app/` is legacy compatibility code and should only be touched when adding temporary shims during the migration.
- `backend/tests/`, `backend/alembic/`, `deploy/`, and `docs/plans/` are part of the active refactor surface.

## Build, Test, and Development Commands
- `cd frontend && npm run dev`: start the Vite dev server.
- `cd frontend && npm test`: run frontend tests with Vitest.
- `cd frontend && npm run build`: build the frontend bundle.
- `cd backend && uv run pytest -q`: run the backend test suite.
- `cd backend && uv run uvicorn app.main:app --reload`: run the current backend entrypoint during migration.
- `docker compose up --build`: start the current stack.
- Prefer targeted backend runs while refactoring, for example: `cd backend && uv run pytest -q tests/test_db_config.py`.

## Coding Style & Naming Conventions
- TypeScript: 2-space indentation, PascalCase components, camelCase functions.
- Python: 4-space indentation, snake_case modules/functions, explicit type hints on new backend code.
- Keep backend business rules out of routers; put them in `application/services` and repository implementations.
- Do not add new flat backend modules under `backend/app/` unless they are migration shims.

## Testing Guidelines
- Follow TDD for backend refactor tasks: write the failing test first, run it, then implement the minimal fix.
- Backend uses Pytest; name files `test_*.py`. Frontend uses Vitest; name files `*.test.ts(x)`.
- Any backend package move must preserve current HTTP behavior unless the plan says otherwise.
- Before claiming completion, run the relevant targeted tests and the final suite for the touched area.

## Commit & Pull Request Guidelines
- Use focused commits with prefixes like `feat:`, `fix:`, `refactor:`, `chore:`.
- Keep refactor commits scoped to one migration stage: settings, DB, routers, Docker, etc.
- PRs should include: scope, migration impact, verification commands, env changes, and screenshots for UI work.

## Architecture & Configuration Rules
- PostgreSQL is the target runtime database; do not introduce new SQLite-first behavior.
- Alembic is the target schema migration path; avoid runtime schema mutation.
- Environment config should converge on grouped variables such as `APP__*`, `AUTH__*`, `DB__*`, `LOG__*`, `OPENROUTER__*`, and `STORAGE__*`.
- Docker assets should converge on `deploy/docker/`, `deploy/compose/`, and `deploy/env/`.
