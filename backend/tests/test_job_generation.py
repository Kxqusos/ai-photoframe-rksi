from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _create_prompt(client: TestClient) -> int:
    payload = {
        "name": "Anime",
        "description": "Soft anime shading",
        "prompt": "Turn input photo into anime portrait",
        "preview_image_url": "/media/previews/anime.jpg",
        "icon_image_url": "/media/icons/anime.png",
    }
    created = client.post("/api/prompts", json=payload)
    assert created.status_code == 201
    return created.json()["id"]


def test_create_job_and_get_completed_result(monkeypatch) -> None:
    _reset_db()

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        assert model
        assert prompt
        assert image_bytes == b"source-image"
        return b"generated-image-bytes"

    monkeypatch.setattr("app.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    files = {"photo": ("photo.jpg", b"source-image", "image/jpeg")}
    data = {"prompt_id": str(prompt_id)}
    created = client.post("/api/jobs", files=files, data=data)
    assert created.status_code == 202

    body = created.json()
    assert body["id"] > 0
    assert body["status"] in {"processing", "completed"}

    status = client.get(f"/api/jobs/{body['id']}")
    assert status.status_code == 200
    status_body = status.json()
    assert status_body["status"] == "completed"
    assert status_body["result_url"].startswith("/qr/")
    assert status_body["download_url"].startswith("/qr/")
