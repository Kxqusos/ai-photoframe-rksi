from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import GenerationJob


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _create_completed_job(client: TestClient, monkeypatch) -> int:
    created_prompt = client.post(
        "/api/prompts",
        json={
            "name": "Comic",
            "description": "Comic style",
            "prompt": "Turn image into comic",
            "preview_image_url": "/media/previews/comic.jpg",
            "icon_image_url": "/media/icons/comic.png",
        },
    )
    assert created_prompt.status_code == 201
    prompt_id = created_prompt.json()["id"]

    monkeypatch.setattr(
        "app.openrouter_client.generate_image",
        lambda **kwargs: b"generated-png-bytes",
    )

    created_job = client.post(
        "/api/jobs",
        files={"photo": ("src.jpg", b"src", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created_job.status_code == 202
    return created_job.json()["id"]


def test_qr_endpoint_returns_png_for_completed_job(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    job_id = _create_completed_job(client, monkeypatch)

    response = client.get(f"/api/jobs/{job_id}/qr")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 20


def test_legacy_download_endpoint_is_not_exposed(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    job_id = _create_completed_job(client, monkeypatch)

    response = client.get(f"/api/jobs/{job_id}/download")
    assert response.status_code == 404


def test_qr_uses_public_base_url_when_configured(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    job_id = _create_completed_job(client, monkeypatch)

    monkeypatch.setenv("QR_PUBLIC_BASE_URL", "https://qr.aiphoto.pups-labs.ru")
    captured: dict[str, str] = {}

    def fake_build_qr_png(url: str) -> bytes:
        captured["url"] = url
        return b"fake-png"

    monkeypatch.setattr("app.routers.jobs.build_qr_png", fake_build_qr_png)

    response = client.get(f"/api/jobs/{job_id}/qr")
    assert response.status_code == 200
    assert response.content == b"fake-png"
    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        assert job is not None
        assert job.qr_hash is not None
        assert captured["url"] == f"https://qr.aiphoto.pups-labs.ru/qr/{job.qr_hash}"


def test_public_qr_hash_endpoint_returns_file(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    job_id = _create_completed_job(client, monkeypatch)

    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        assert job is not None
        assert job.qr_hash is not None
        qr_hash = job.qr_hash

    response = client.get(f"/qr/{qr_hash}")
    assert response.status_code == 200
    assert response.content == b"generated-png-bytes"
