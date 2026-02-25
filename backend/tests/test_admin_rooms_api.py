from pathlib import Path

from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _configure_admin_credentials(monkeypatch) -> tuple[str, str]:
    from app.auth import password_context, settings

    username = "admin"
    password = "super-secret-password"
    password_hash = password_context.hash(password)

    monkeypatch.setattr(settings, "admin_username", username)
    monkeypatch.setattr(settings, "admin_password", "")
    monkeypatch.setattr(settings, "admin_password_hash", password_hash)
    monkeypatch.setattr(settings, "jwt_secret", "test-jwt-secret-with-at-least-32-bytes")
    monkeypatch.setattr(settings, "jwt_expire_minutes", 60)
    return username, password


def _get_admin_token(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/admin/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_rooms_crud_and_model_update_requires_jwt(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)

    unauthorized = client.get("/api/admin/rooms")
    assert unauthorized.status_code == 401

    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "room-a", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    listed = client.get("/api/admin/rooms", headers=headers)
    assert listed.status_code == 200
    assert any(room["slug"] == "room-a" for room in listed.json())

    updated = client.put(
        f"/api/admin/rooms/{room_id}",
        headers=headers,
        json={"slug": "room-a", "name": "Room A Updated", "model_name": "openai/gpt-5-image", "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Room A Updated"
    assert updated.json()["is_active"] is False

    model_updated = client.put(
        f"/api/admin/rooms/{room_id}/model",
        headers=headers,
        json={"model_name": "google/gemini-2.5-flash-image"},
    )
    assert model_updated.status_code == 200
    assert model_updated.json()["model_name"] == "google/gemini-2.5-flash-image"


def test_admin_room_prompt_endpoints_are_scoped(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    room_a = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "room-a", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    room_b = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "room-b", "name": "Room B", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert room_a.status_code == 201
    assert room_b.status_code == 201
    room_a_id = room_a.json()["id"]
    room_b_id = room_b.json()["id"]

    created_prompt = client.post(
        f"/api/admin/rooms/{room_a_id}/prompts",
        headers=headers,
        json={
            "name": "Prompt A",
            "description": "desc",
            "prompt": "prompt body",
            "preview_image_url": "/media/previews/a.jpg",
            "icon_image_url": "/media/icons/a.png",
        },
    )
    assert created_prompt.status_code == 201
    prompt_id = created_prompt.json()["id"]

    room_a_prompts = client.get(f"/api/admin/rooms/{room_a_id}/prompts", headers=headers)
    room_b_prompts = client.get(f"/api/admin/rooms/{room_b_id}/prompts", headers=headers)
    assert room_a_prompts.status_code == 200
    assert room_b_prompts.status_code == 200
    assert len(room_a_prompts.json()) == 1
    assert room_b_prompts.json() == []

    wrong_delete = client.delete(f"/api/admin/rooms/{room_b_id}/prompts/{prompt_id}", headers=headers)
    assert wrong_delete.status_code == 404

    deleted = client.delete(f"/api/admin/rooms/{room_a_id}/prompts/{prompt_id}", headers=headers)
    assert deleted.status_code == 204


def test_admin_room_media_uploads_are_room_scoped(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    preview_dir = tmp_path / "previews"
    icon_dir = tmp_path / "icons"
    monkeypatch.setattr("app.routers.media.PREVIEW_DIR", preview_dir)
    monkeypatch.setattr("app.routers.media.ICON_DIR", icon_dir)

    room = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "room-media", "name": "Room Media", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert room.status_code == 201
    room_id = room.json()["id"]

    preview_upload = client.post(
        f"/api/admin/rooms/{room_id}/media/prompt-preview",
        headers=headers,
        files={"file": ("preview.jpg", b"preview-bytes", "image/jpeg")},
    )
    assert preview_upload.status_code == 201
    assert preview_upload.json()["url"].startswith(f"/media/previews/room-{room_id}/")

    icon_upload = client.post(
        f"/api/admin/rooms/{room_id}/media/prompt-icon",
        headers=headers,
        files={"file": ("icon.png", b"icon-bytes", "image/png")},
    )
    assert icon_upload.status_code == 201
    assert icon_upload.json()["url"].startswith(f"/media/icons/room-{room_id}/")
