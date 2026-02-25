# Room System Rollout Notes

## Scope
- Room-first public API (`/api/rooms/{slug}/*`).
- JWT-protected admin API (`/api/admin/*`).
- Backward compatibility wrappers for legacy default-room endpoints.

## Migration checklist
- [x] `rooms` table and `room_id` foreign keys added.
- [x] Default room auto-created and used for legacy wrappers.
- [x] Room-scoped prompt/job/gallery/hash APIs available.
- [x] Admin JWT login and protected room management APIs available.
- [x] Frontend public routes are room-aware.
- [x] Frontend admin pages use JWT auth.

## Backward compatibility removal checklist
Keep these until clients fully migrate to room-scoped API:
- [ ] Remove `GET /api/prompts` wrapper.
- [ ] Remove `POST /api/jobs` wrapper.
- [ ] Remove `GET /api/jobs/{job_id}` wrapper.
- [ ] Remove `GET /api/jobs/{job_id}/qr` wrapper.
- [ ] Remove `GET /api/jobs/hash/{jpg_hash}` wrapper.
- [ ] Remove `GET /api/jobs/gallery` wrapper.
- [ ] Remove legacy `/api/settings/model` endpoint once admin room model management is the only path.

## Security checklist
- [x] Admin endpoints require `Authorization: Bearer <token>`.
- [x] Token signature and expiration are validated.
- [x] Public room endpoints reject missing/inactive room slug.
- [x] Room ownership checks enforced for prompt/job access.

## Verification evidence
### Task 8 docs contract
- `cd backend && uv run pytest tests/test_docs_room_contract.py tests/test_docs_contract.py -q`
- Result: pass (`2 passed in 0.01s`).

### Task 9 full verification
- `cd backend && uv run pytest -q`
- Result: pending.
- `cd frontend && npm test -- --run`
- Result: pending.

### Manual smoke checks
- Admin login (`/admin/login`): pending.
- Create two rooms and separate prompts/models: pending.
- Room gallery/hash isolation: pending.
