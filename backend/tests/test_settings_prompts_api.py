from fastapi.testclient import TestClient

from photoframe_backend.infrastructure.db.base import Base
from photoframe_backend.infrastructure.db.session import engine
from photoframe_backend.main import app


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_create_and_list_prompt() -> None:
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
    assert created.status_code == 201

    listed = client.get("/api/prompts")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["name"] == "Anime"


def test_delete_prompt() -> None:
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
    assert created.status_code == 201
    prompt_id = created.json()["id"]

    deleted = client.delete(f"/api/prompts/{prompt_id}")
    assert deleted.status_code == 204

    listed = client.get("/api/prompts")
    assert listed.status_code == 200
    assert listed.json() == []


def test_set_and_get_model() -> None:
    _reset_db()
    client = TestClient(app)

    updated = client.put("/api/settings/model", json={"model_name": "openai/gpt-5-image"})
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


def test_schema_compat_module_reexports_src_api_models() -> None:
    import photoframe_backend.api.http.schemas as legacy_schemas
    from photoframe_backend.api.http.schemas.admin import RoomCreate
    from photoframe_backend.api.http.schemas.public import ModelSettingIn

    assert legacy_schemas.RoomCreate is RoomCreate
    assert legacy_schemas.ModelSettingIn is ModelSettingIn
