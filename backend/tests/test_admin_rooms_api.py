import re
from pathlib import Path

from fastapi.testclient import TestClient

from photoframe_backend.infrastructure.db.base import Base
from photoframe_backend.infrastructure.db.session import engine
from photoframe_backend.main import app


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _configure_admin_credentials(monkeypatch) -> tuple[str, str]:
    from photoframe_backend.api.http.security import settings

    username = "admin"
    password = "super-secret-password"

    monkeypatch.setattr(settings.auth, "admin_username", username)
    monkeypatch.setattr(settings.auth, "admin_password", password)
    monkeypatch.setattr(settings.auth, "jwt_secret", "test-jwt-secret-with-at-least-32-bytes")
    monkeypatch.setattr(settings.auth, "jwt_expire_minutes", 60)
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
        json={
            "slug": "aaaaaaaa",
            "name": "Room A",
            "model_name": "openai/gpt-5-image",
            "is_active": True,
            "password": "room-a-pass",
        },
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    listed = client.get("/api/admin/rooms", headers=headers)
    assert listed.status_code == 200
    assert any(room["slug"] == "aaaaaaaa" for room in listed.json())

    updated = client.patch(
        f"/api/admin/rooms/{room_id}",
        headers=headers,
        json={
            "slug": "aaaaaaaa",
            "name": "Room A Updated",
            "model_name": "openai/gpt-5-image",
            "is_active": False,
            "password": "room-a-pass-updated",
        },
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


def test_admin_room_delete_removes_room(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={
            "slug": "dddddddd",
            "name": "Room D",
            "model_name": "openai/gpt-5-image",
            "is_active": True,
            "password": "room-d-pass",
        },
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    deleted = client.delete(f"/api/admin/rooms/{room_id}", headers=headers)
    assert deleted.status_code == 204

    listed = client.get("/api/admin/rooms", headers=headers)
    assert listed.status_code == 200
    assert all(room["id"] != room_id for room in listed.json())


def test_admin_room_delete_rejects_default_room(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={
            "slug": "ph000000",
            "name": "Main",
            "model_name": "openai/gpt-5-image",
            "is_active": True,
            "password": "main-pass",
        },
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    deleted = client.delete(f"/api/admin/rooms/{room_id}", headers=headers)
    assert deleted.status_code == 409
    assert deleted.json()["detail"] == "default room cannot be deleted"


def test_admin_room_delete_rejects_room_with_prompts(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={
            "slug": "eeeeeeee",
            "name": "Room E",
            "model_name": "openai/gpt-5-image",
            "is_active": True,
            "password": "room-e-pass",
        },
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    prompt_created = client.post(
        f"/api/admin/rooms/{room_id}/prompts",
        headers=headers,
        json={
            "name": "Prompt E",
            "description": "desc",
            "prompt": "prompt body",
            "preview_image_url": "/media/previews/e.jpg",
            "icon_image_url": "/media/icons/e.png",
        },
    )
    assert prompt_created.status_code == 201

    deleted = client.delete(f"/api/admin/rooms/{room_id}", headers=headers)
    assert deleted.status_code == 409
    assert deleted.json()["detail"] == "room cannot be deleted while prompts exist"


def test_admin_room_prompt_endpoints_are_scoped(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    room_a = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={
            "slug": "aaaaaaaa",
            "name": "Room A",
            "model_name": "openai/gpt-5-image",
            "is_active": True,
            "password": "room-a-pass",
        },
    )
    room_b = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={
            "slug": "bbbbbbbb",
            "name": "Room B",
            "model_name": "openai/gpt-5-image",
            "is_active": True,
            "password": "room-b-pass",
        },
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
    monkeypatch.setattr("photoframe_backend.api.http.routers.media.PREVIEW_DIR", preview_dir)
    monkeypatch.setattr("photoframe_backend.api.http.routers.media.ICON_DIR", icon_dir)

    room = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={
            "slug": "cccccccc",
            "name": "Room Media",
            "model_name": "openai/gpt-5-image",
            "is_active": True,
            "password": "room-media-pass",
        },
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


def test_admin_room_rejects_invalid_slug_format(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    invalid = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={
            "slug": "room-a",
            "name": "Room A",
            "model_name": "openai/gpt-5-image",
            "is_active": True,
            "password": "room-a-pass",
        },
    )
    assert invalid.status_code == 422


def test_admin_room_auto_generates_slug_when_missing(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"name": "Room Auto", "model_name": "openai/gpt-5-image", "is_active": True, "password": "room-auto-pass"},
    )
    assert created.status_code == 201
    body = created.json()
    assert re.fullmatch(r"[a-z0-9]{8}", body["slug"])


def test_admin_room_creation_requires_password(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "ffffffff", "name": "Room F", "model_name": "openai/gpt-5-image", "is_active": True},
    )

    assert created.status_code == 422


def test_admin_router_is_sourced_from_src_api_layer() -> None:
    from photoframe_backend.api.http.routers.admin import router as src_admin_router
    from photoframe_backend.main import app as src_app

    route_paths = {route.path for route in src_admin_router.routes}
    app_paths = {route.path for route in src_app.routes}

    assert "/api/admin/rooms" in route_paths
    assert route_paths <= app_paths
