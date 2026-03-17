# API Contract

Runtime entrypoint: `uv run uvicorn photoframe_backend.main:app --reload`

## Health
- `GET /api/health` -> `{ "status": "ok" }`

## Public Room API (recommended)
- `GET /api/rooms` -> active public rooms (`id`, `slug`, `name`) for room selector menu.
- `POST /api/rooms/{slug}/access` with JSON `{ "password": "..." }` -> `{ "access_token": "...", "token_type": "bearer" }`
- Room-scoped endpoints below require header `X-Room-Access-Token: <token>`
- `GET /api/rooms/{slug}/prompts` -> prompt styles for active room.
- `POST /api/rooms/{slug}/jobs` (multipart: `photo`, `prompt_id`) -> `{ "id": "8-char-token", "status": "processing" }`
- `GET /api/rooms/{slug}/jobs/hash/{jpg_hash}` -> room-scoped job status.
- `GET /api/rooms/{slug}/jobs/gallery` -> completed generated images for room.
- `GET /qr/{qr_hash}` -> downloadable generated image file.

### Job status response shape
- `id`
- `status` (`processing` | `completed` | `error`)
- `result_url` (for completed jobs, points to `/qr/{qr_hash}`)
- `download_url` (for completed jobs, points to `/qr/{qr_hash}`)
- `qr_url` (PNG endpoint for hash-based status route)
- `error_message`

## Legacy compatibility wrappers (default room)
- `GET /api/prompts`
- `POST /api/prompts` with `Authorization: Bearer <token>`
- `DELETE /api/prompts/{prompt_id}` with `Authorization: Bearer <token>`
- `POST /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/qr`
- `GET /api/jobs/hash/{jpg_hash}`
- `GET /api/jobs/hash/{jpg_hash}/qr`
- `GET /api/jobs/gallery`

These wrappers resolve to the default public room and are kept for backward compatibility.

## Admin Auth (JWT Bearer)
- `POST /api/admin/auth/login` with JSON:
  - `username`
  - `password`
  -> `{ "access_token": "...", "token_type": "bearer" }`
- `GET /api/admin/auth/me` with header `Authorization: Bearer <token>` -> `{ "username": "..." }`

Missing/invalid token returns `401` with `WWW-Authenticate: Bearer`.
Insecure admin auth configuration returns `503` on login/protected auth flows.

## Admin Room Management (JWT required)
All endpoints below require `Authorization: Bearer <token>`.

- `GET /api/admin/rooms` -> list rooms.
- `POST /api/admin/rooms` with JSON:
  - `name`
  - `model_name`
  - `is_active`
  - `password`
  - `slug` (optional; when omitted, backend auto-generates an 8-char slug `[a-z0-9]`)
- `PATCH /api/admin/rooms/{room_id}` with any subset of:
  - `slug`
  - `name`
  - `model_name`
  - `is_active`
  - `password`
- `DELETE /api/admin/rooms/{room_id}` for empty non-default rooms.
- `PUT /api/admin/rooms/{room_id}/model` with JSON `{ "model_name": "..." }`.
- `GET /api/admin/rooms/{room_id}/prompts`
- `POST /api/admin/rooms/{room_id}/prompts`
- `DELETE /api/admin/rooms/{room_id}/prompts/{prompt_id}`
- `POST /api/admin/rooms/{room_id}/media/prompt-preview` (multipart `file`, image only, size-limited)
- `POST /api/admin/rooms/{room_id}/media/prompt-icon` (multipart `file`, image only, size-limited)

## Legacy model setting endpoint
- `GET /api/settings/model`
- `PUT /api/settings/model` with `Authorization: Bearer <token>`
