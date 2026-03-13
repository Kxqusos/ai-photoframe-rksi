import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import GenerationJob
from tests.image_utils import tiny_jpeg_bytes, tiny_png_bytes


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _configure_admin_credentials(monkeypatch) -> tuple[str, str]:
    from app.auth import settings

    username = "admin"
    password = "super-secret-password"

    monkeypatch.setattr(settings, "admin_username", username)
    monkeypatch.setattr(settings, "admin_password", password)
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
        json={"slug": "aaaaaaaa", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    listed = client.get("/api/admin/rooms", headers=headers)
    assert listed.status_code == 200
    assert any(room["slug"] == "aaaaaaaa" for room in listed.json())

    updated = client.put(
        f"/api/admin/rooms/{room_id}",
        headers=headers,
        json={"slug": "aaaaaaaa", "name": "Room A Updated", "model_name": "openai/gpt-5-image", "is_active": False},
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


def test_admin_room_patch_updates_only_requested_fields(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "aaaaaaaa", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    patched = client.patch(
        f"/api/admin/rooms/{room_id}",
        headers=headers,
        json={"name": "Room A Updated", "is_active": False},
    )
    assert patched.status_code == 200
    assert patched.json() == {
        "id": room_id,
        "slug": "aaaaaaaa",
        "name": "Room A Updated",
        "model_name": "openai/gpt-5-image",
        "is_active": False,
    }


def test_admin_room_patch_rejects_duplicate_slug(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    room_a = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "aaaaaaaa", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    room_b = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "bbbbbbbb", "name": "Room B", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert room_a.status_code == 201
    assert room_b.status_code == 201

    patched = client.patch(
        f"/api/admin/rooms/{room_b.json()['id']}",
        headers=headers,
        json={"slug": "aaaaaaaa"},
    )
    assert patched.status_code == 409


def test_admin_room_delete_removes_empty_non_default_room(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "aaaaaaaa", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    deleted = client.delete(f"/api/admin/rooms/{room_id}", headers=headers)
    assert deleted.status_code == 204

    listed = client.get("/api/admin/rooms", headers=headers)
    assert listed.status_code == 200
    assert all(room["id"] != room_id for room in listed.json())


def test_admin_room_delete_rejects_default_room_and_rooms_with_dependencies(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    created_default = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "ph000000", "name": "Main", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert created_default.status_code == 201
    default_room = created_default.json()

    default_delete = client.delete(f"/api/admin/rooms/{default_room['id']}", headers=headers)
    assert default_delete.status_code == 409

    created_room = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "aaaaaaaa", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert created_room.status_code == 201
    room_id = created_room.json()["id"]

    created_prompt = client.post(
        f"/api/admin/rooms/{room_id}/prompts",
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

    with SessionLocal() as db:
        db.add(GenerationJob(prompt_id=prompt_id, room_id=room_id, status="completed"))
        db.commit()

    occupied_delete = client.delete(f"/api/admin/rooms/{room_id}", headers=headers)
    assert occupied_delete.status_code == 409


def test_admin_room_prompt_endpoints_are_scoped(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    room_a = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "aaaaaaaa", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    room_b = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "bbbbbbbb", "name": "Room B", "model_name": "openai/gpt-5-image", "is_active": True},
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


def test_admin_room_prompt_can_be_updated(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    room = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "editroom", "name": "Room Edit", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert room.status_code == 201
    room_id = room.json()["id"]
    other_room = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "othrroom", "name": "Room Other", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert other_room.status_code == 201
    other_room_id = other_room.json()["id"]

    created_prompt = client.post(
        f"/api/admin/rooms/{room_id}/prompts",
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

    wrong_room_update = client.put(
        f"/api/admin/rooms/{other_room_id}/prompts/{prompt_id}",
        headers=headers,
        json={
            "name": "Prompt B",
            "description": "updated desc",
            "prompt": "updated prompt body",
            "preview_image_url": "/media/previews/b.jpg",
            "icon_image_url": "/media/icons/b.png",
        },
    )
    assert wrong_room_update.status_code == 404

    updated = client.put(
        f"/api/admin/rooms/{room_id}/prompts/{prompt_id}",
        headers=headers,
        json={
            "name": "Prompt B",
            "description": "updated desc",
            "prompt": "updated prompt body",
            "preview_image_url": "/media/previews/b.jpg",
            "icon_image_url": "/media/icons/b.png",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Prompt B"
    assert updated.json()["description"] == "updated desc"
    assert updated.json()["prompt"] == "updated prompt body"
    assert updated.json()["preview_image_url"] == "/media/previews/b.jpg"
    assert updated.json()["icon_image_url"] == "/media/icons/b.png"

    listed = client.get(f"/api/admin/rooms/{room_id}/prompts", headers=headers)
    assert listed.status_code == 200
    assert listed.json() == [
        {
            "id": prompt_id,
            "name": "Prompt B",
            "description": "updated desc",
            "prompt": "updated prompt body",
            "preview_image_url": "/media/previews/b.jpg",
            "icon_image_url": "/media/icons/b.png",
        }
    ]


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
        json={"slug": "cccccccc", "name": "Room Media", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert room.status_code == 201
    room_id = room.json()["id"]

    preview_upload = client.post(
        f"/api/admin/rooms/{room_id}/media/prompt-preview",
        headers=headers,
        files={"file": ("preview.jpg", tiny_jpeg_bytes(), "image/jpeg")},
    )
    assert preview_upload.status_code == 201
    assert preview_upload.json()["url"].startswith(f"/media/previews/room-{room_id}/")

    icon_upload = client.post(
        f"/api/admin/rooms/{room_id}/media/prompt-icon",
        headers=headers,
        files={"file": ("icon.png", tiny_png_bytes(), "image/png")},
    )
    assert icon_upload.status_code == 201
    assert icon_upload.json()["url"].startswith(f"/media/icons/room-{room_id}/")


def test_admin_room_media_uploads_reject_non_image(monkeypatch, tmp_path: Path) -> None:
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
        json={"slug": "dddddddd", "name": "Room Media", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert room.status_code == 201
    room_id = room.json()["id"]

    response = client.post(
        f"/api/admin/rooms/{room_id}/media/prompt-preview",
        headers=headers,
        files={"file": ("preview.html", b"<h1>x</h1>", "text/html")},
    )
    assert response.status_code == 400


def test_admin_room_rejects_invalid_slug_format(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    invalid = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "room-a", "name": "Room A", "model_name": "openai/gpt-5-image", "is_active": True},
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
        json={"name": "Room Auto", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert created.status_code == 201
    body = created.json()
    assert re.fullmatch(r"[a-z0-9]{8}", body["slug"])


def test_admin_room_rejects_blank_name_and_too_long_model_name(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    blank_name = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "eeeeeeee", "name": "   ", "model_name": "openai/gpt-5-image", "is_active": True},
    )
    assert blank_name.status_code == 422

    too_long_model = client.post(
        "/api/admin/rooms",
        headers=headers,
        json={"slug": "ffffffff", "name": "Room", "model_name": "m" * 256, "is_active": True},
    )
    assert too_long_model.status_code == 422
