# Run Local

## Requirements
- Python 3.14+
- Node.js 20+
- `uv`

## Backend
1. `cd backend`
2. `cp .env.example .env` and fill values
   - For faster generation routing: keep `OPENROUTER_PROVIDER_SORT=throughput` and tune `OPENROUTER_PREFERRED_MAX_LATENCY` (seconds).
   - Source image is preprocessed before OpenRouter call (`OPENROUTER_SOURCE_MAX_SIDE`, `OPENROUTER_SOURCE_JPEG_QUALITY`).
   - If OpenRouter returns a response without image data, backend retries automatically (`OPENROUTER_MISSING_IMAGE_RETRIES`).
   - Generated output is JPEG by default (`OPENROUTER_RESULT_FORMAT=jpeg`, quality via `OPENROUTER_JPEG_QUALITY`).
   - Generated files are stored for `RESULT_RETENTION_DAYS` and then pruned.
   - Backend writes logs to `backend/logs/backend.log` by default (`LOG_FILE_PATH`).
   - JWT/admin setup:
     - `JWT_SECRET` must be non-default in non-local environments.
     - `ADMIN_USERNAME` and `ADMIN_PASSWORD` configure single admin account.
     - `ADMIN_PASSWORD_HASH` is optional legacy fallback (used only when `ADMIN_PASSWORD` is empty).
     - `DEFAULT_PUBLIC_ROOM_SLUG` controls which room legacy wrappers (`/api/jobs`, `/api/prompts`) point to.
3. `uv run uvicorn app.main:app --reload`

Backend starts at `http://127.0.0.1:8000`.

## Frontend
1. `cd frontend`
2. `cp .env.example .env` (optional)
3. `npm install`
4. `npm run dev`

Frontend starts at `http://127.0.0.1:5173`.

## End-to-end check
1. Open `/admin/login`, sign in with `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
2. In `/admin`, create two rooms (for example `room-a`, `room-b`) with different models.
3. In each room editor, create prompts and upload preview/icon media.
4. Open `/main` (or another room slug), upload a photo, and generate an image.
5. Open `/main/gallery` and verify only that room's results are shown.
6. Resolve status via `GET /api/rooms/main/jobs/hash/{jpg_hash}` and confirm room scoping.
7. Verify `/qr/{qr_hash}` downloads generated file.
