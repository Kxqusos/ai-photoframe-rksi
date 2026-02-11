# Run Local

## Requirements
- Python 3.14+
- Node.js 20+
- `uv`

## Backend
1. `cd backend`
2. `cp .env.example .env` and fill values
3. `uv run uvicorn app.main:app --reload`

Backend starts at `http://127.0.0.1:8000`.

## Frontend
1. `cd frontend`
2. `cp .env.example .env` (optional)
3. `npm install`
4. `npm run dev`

Frontend starts at `http://127.0.0.1:5173`.

## End-to-end check
1. Open `/settings`, choose model, add style prompt with preview + icon.
2. Open `/`, upload a photo and pick style.
3. Wait for result page.
4. Verify QR image loads and encoded URL points to `/qr/{qr_hash}`.
5. Open `/qr/{qr_hash}` and confirm the file downloads.
