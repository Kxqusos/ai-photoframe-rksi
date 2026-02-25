# API Contract

## Health
- `GET /api/health` -> `{ "status": "ok" }`

## Public Room API (recommended)
- `GET /api/rooms` -> active public rooms (`id`, `slug`, `name`) for room selector menu.
- `GET /api/rooms/{slug}/prompts` -> prompt styles for active room.
- `POST /api/rooms/{slug}/jobs` (multipart: `photo`, `prompt_id`) -> `{ "id": number, "status": "processing" }`
- `GET /api/rooms/{slug}/jobs/hash/{jpg_hash}` -> room-scoped job status.
- `GET /api/rooms/{slug}/jobs/gallery` -> completed generated images for room.
- `GET /qr/{qr_hash}` -> downloadable generated image file.

### Job status response shape
- `id`
- `status` (`processing` | `completed` | `error`)
- `result_url` (for completed jobs, points to `/qr/{qr_hash}`)
- `download_url` (for completed jobs, points to `/qr/{qr_hash}`)
- `qr_url` (PNG endpoint for legacy status route)
- `error_message`

## Legacy compatibility wrappers (default room)
- `GET /api/prompts`
- `POST /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/qr`
- `GET /api/jobs/hash/{jpg_hash}`
- `GET /api/jobs/gallery`

These wrappers resolve to the default public room and are kept for backward compatibility during migration.

## Admin Auth (JWT Bearer)
- `POST /api/admin/auth/login` with JSON:
  - `username`
  - `password`
  -> `{ "access_token": "...", "token_type": "bearer" }`
- `GET /api/admin/auth/me` with header `Authorization: Bearer <token>` -> `{ "username": "..." }`

Missing/invalid token returns `401` with `WWW-Authenticate: Bearer`.

## Admin Room Management (JWT required)
All endpoints below require `Authorization: Bearer <token>`.

- `GET /api/admin/rooms` -> list rooms.
- `POST /api/admin/rooms` with JSON:
  - `slug`
  - `name`
  - `model_name`
  - `is_active`
- `PUT /api/admin/rooms/{room_id}` with same JSON fields as create.
- `PUT /api/admin/rooms/{room_id}/model` with JSON `{ "model_name": "..." }`.
- `GET /api/admin/rooms/{room_id}/prompts`
- `POST /api/admin/rooms/{room_id}/prompts`
- `DELETE /api/admin/rooms/{room_id}/prompts/{prompt_id}`
- `POST /api/admin/rooms/{room_id}/media/prompt-preview` (multipart `file`)
- `POST /api/admin/rooms/{room_id}/media/prompt-icon` (multipart `file`)

## Legacy model setting endpoint
- `GET /api/settings/model`
- `PUT /api/settings/model`
