from fastapi.testclient import TestClient

from app.main import app
from tests.image_utils import tiny_jpeg_bytes, tiny_png_bytes


def test_upload_prompt_preview_image() -> None:
    client = TestClient(app)

    files = {"file": ("preview.jpg", tiny_jpeg_bytes(), "image/jpeg")}
    response = client.post("/api/media/prompt-preview", files=files)
    assert response.status_code == 201
    body = response.json()
    assert body["url"].startswith("/media/previews/")


def test_upload_prompt_icon_image() -> None:
    client = TestClient(app)

    files = {"file": ("icon.png", tiny_png_bytes(), "image/png")}
    response = client.post("/api/media/prompt-icon", files=files)
    assert response.status_code == 201
    body = response.json()
    assert body["url"].startswith("/media/icons/")


def test_upload_prompt_preview_rejects_non_image_file() -> None:
    client = TestClient(app)

    response = client.post("/api/media/prompt-preview", files={"file": ("preview.html", b"<h1>x</h1>", "text/html")})

    assert response.status_code == 400


def test_upload_prompt_preview_rejects_oversized_file(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr("app.routers.media.MAX_UPLOAD_BYTES", 4)

    response = client.post("/api/media/prompt-preview", files={"file": ("preview.jpg", tiny_jpeg_bytes(), "image/jpeg")})

    assert response.status_code == 413
