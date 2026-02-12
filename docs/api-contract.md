# API Contract

## Health
- `GET /api/health` -> `{ "status": "ok" }`

## Settings
- `GET /api/settings/model` -> current OpenRouter model
- `PUT /api/settings/model` with JSON `{ "model_name": "..." }` -> saved model

## Prompts
- `GET /api/prompts` -> list of prompt styles
- `POST /api/prompts` with JSON:
  - `name`
  - `description`
  - `prompt`
  - `preview_image_url`
  - `icon_image_url`

## Media
- `POST /api/media/prompt-preview` (multipart `file`) -> `{ "url": "/media/previews/..." }`
- `POST /api/media/prompt-icon` (multipart `file`) -> `{ "url": "/media/icons/..." }`

## Jobs
- `POST /api/jobs` (multipart: `photo`, `prompt_id`) -> `{ "id": number, "status": "processing" }` (generation continues in background)
- `GET /api/jobs/{job_id}` ->
  - `status`
  - `result_url` (for completed jobs, points to `/qr/{qr_hash}`)
  - `download_url` (for completed jobs, points to `/qr/{qr_hash}`)
  - `qr_url` (PNG endpoint)
  - `error_message`
- `GET /api/jobs/{job_id}/qr` -> PNG QR code that encodes a public `/qr/{qr_hash}` link

## Public download
- `GET /qr/{qr_hash}` -> downloadable generated image file
