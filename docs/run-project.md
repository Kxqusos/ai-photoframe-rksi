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
- `OPENROUTER_API_KEY`
- `JWT_SECRET`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD_HASH`
- `DEFAULT_PUBLIC_ROOM_SLUG` (usually `main`)

Generate bcrypt hash for admin password:
```bash
cd backend
uv run python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt'], deprecated='auto').hash('change-me'))"
```

Run API:
```bash
cd backend
uv run uvicorn app.main:app --reload
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
3. Open `/{room_slug}` (for example `/main`) and run generation.
4. Verify gallery isolation at `/{room_slug}/gallery`.

## Notes
- Legacy wrappers (`/api/prompts`, `/api/jobs/*`) still map to default room.
- For full details, see `docs/run-local.md`.
