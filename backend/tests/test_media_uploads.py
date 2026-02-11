from fastapi.testclient import TestClient

from app.main import app


def test_upload_prompt_preview_image() -> None:
    client = TestClient(app)

    files = {"file": ("preview.jpg", b"fake-image-bytes", "image/jpeg")}
    response = client.post("/api/media/prompt-preview", files=files)
    assert response.status_code == 201
    body = response.json()
    assert body["url"].startswith("/media/previews/")


def test_upload_prompt_icon_image() -> None:
    client = TestClient(app)

    files = {"file": ("icon.png", b"icon-image-bytes", "image/png")}
    response = client.post("/api/media/prompt-icon", files=files)
    assert response.status_code == 201
    body = response.json()
    assert body["url"].startswith("/media/icons/")
