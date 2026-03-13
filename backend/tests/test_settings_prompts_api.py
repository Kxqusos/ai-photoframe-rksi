from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


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


def _get_admin_headers(client: TestClient, monkeypatch) -> dict[str, str]:
    username, password = _configure_admin_credentials(monkeypatch)
    response = client.post("/api/admin/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_create_and_list_prompt(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    headers = _get_admin_headers(client, monkeypatch)

    payload = {
        "name": "Anime",
        "description": "Soft anime shading",
        "prompt": "Turn input photo into anime portrait",
        "preview_image_url": "/media/previews/anime.jpg",
        "icon_image_url": "/media/icons/anime.png",
    }

    created = client.post("/api/prompts", json=payload, headers=headers)
    assert created.status_code == 201

    listed = client.get("/api/prompts")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["name"] == "Anime"


def test_delete_prompt(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    headers = _get_admin_headers(client, monkeypatch)

    payload = {
        "name": "Anime",
        "description": "Soft anime shading",
        "prompt": "Turn input photo into anime portrait",
        "preview_image_url": "/media/previews/anime.jpg",
        "icon_image_url": "/media/icons/anime.png",
    }

    created = client.post("/api/prompts", json=payload, headers=headers)
    assert created.status_code == 201
    prompt_id = created.json()["id"]

    deleted = client.delete(f"/api/prompts/{prompt_id}", headers=headers)
    assert deleted.status_code == 204

    listed = client.get("/api/prompts")
    assert listed.status_code == 200
    assert listed.json() == []


def test_set_and_get_model(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    headers = _get_admin_headers(client, monkeypatch)

    updated = client.put("/api/settings/model", json={"model_name": "openai/gpt-5-image"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["model_name"] == "openai/gpt-5-image"

    current = client.get("/api/settings/model")
    assert current.status_code == 200
    assert current.json()["model_name"] == "openai/gpt-5-image"


def test_get_model_returns_new_default_model() -> None:
    _reset_db()
    client = TestClient(app)

    current = client.get("/api/settings/model")
    assert current.status_code == 200
    assert current.json()["model_name"] == "openai/gpt-5-image"


def test_legacy_prompt_write_endpoints_require_admin_jwt(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)

    payload = {
        "name": "Anime",
        "description": "Soft anime shading",
        "prompt": "Turn input photo into anime portrait",
        "preview_image_url": "/media/previews/anime.jpg",
        "icon_image_url": "/media/icons/anime.png",
    }

    created = client.post("/api/prompts", json=payload)
    assert created.status_code == 401

    headers = _get_admin_headers(client, monkeypatch)
    created = client.post("/api/prompts", json=payload, headers=headers)
    assert created.status_code == 201

    deleted = client.delete(f"/api/prompts/{created.json()['id']}")
    assert deleted.status_code == 401


def test_set_model_requires_admin_jwt() -> None:
    _reset_db()
    client = TestClient(app)

    response = client.put("/api/settings/model", json={"model_name": "openai/gpt-5-image"})
    assert response.status_code == 401


def test_prompt_payload_rejects_blank_and_oversized_fields(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    headers = _get_admin_headers(client, monkeypatch)

    blank_name = client.post(
        "/api/prompts",
        headers=headers,
        json={
            "name": "   ",
            "description": "desc",
            "prompt": "prompt",
            "preview_image_url": "/media/previews/a.jpg",
            "icon_image_url": "/media/icons/a.png",
        },
    )
    assert blank_name.status_code == 422

    oversized_description = client.post(
        "/api/prompts",
        headers=headers,
        json={
            "name": "Anime",
            "description": "d" * 501,
            "prompt": "prompt",
            "preview_image_url": "/media/previews/a.jpg",
            "icon_image_url": "/media/icons/a.png",
        },
    )
    assert oversized_description.status_code == 422
