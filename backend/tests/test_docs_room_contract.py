from pathlib import Path


def test_docs_cover_room_and_admin_contract() -> None:
    api_contract = Path("../docs/api-contract.md").read_text(encoding="utf-8")
    run_local = Path("../docs/run-local.md").read_text(encoding="utf-8")
    backend_env = Path(".env.example").read_text(encoding="utf-8")
    frontend_env = Path("../frontend/.env.example").read_text(encoding="utf-8")

    assert "GET /api/rooms/{slug}/prompts" in api_contract
    assert "POST /api/rooms/{slug}/jobs" in api_contract
    assert "GET /api/rooms/{slug}/jobs/gallery" in api_contract
    assert "GET /api/rooms/{slug}/jobs/hash/{jpg_hash}" in api_contract

    assert "POST /api/admin/auth/login" in api_contract
    assert "GET /api/admin/auth/me" in api_contract
    assert "GET /api/admin/rooms" in api_contract
    assert "PUT /api/admin/rooms/{room_id}" in api_contract
    assert "PUT /api/admin/rooms/{room_id}/model" in api_contract

    assert "ADMIN_USERNAME" in backend_env
    assert "ADMIN_PASSWORD" in backend_env
    assert "JWT_SECRET" in backend_env
    assert "JWT_EXPIRE_MINUTES" in backend_env
    assert "DEFAULT_PUBLIC_ROOM_SLUG" in backend_env

    assert "ADMIN_PASSWORD" in run_local
    assert "/main" in run_local
    assert "/admin/login" in run_local

    assert "VITE_DEFAULT_ROOM_SLUG" in frontend_env
