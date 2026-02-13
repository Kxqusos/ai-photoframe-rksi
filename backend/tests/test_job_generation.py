import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.job_service import DEFAULT_MODEL_NAME, LEGACY_MODEL_NAME, LEGACY_OPENAI_MODEL_NAME
from app.main import app
from app.models import GenerationJob


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


def _patch_storage_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    source_dir = tmp_path / "source"
    result_dir = tmp_path / "results"
    source_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.job_service.SOURCE_DIR", source_dir)
    monkeypatch.setattr("app.job_service.RESULT_DIR", result_dir)
    return source_dir, result_dir


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
    assert body["status"] == "processing"

    status_body: dict[str, str] | None = None
    for _ in range(30):
        status = client.get(f"/api/jobs/{body['id']}")
        assert status.status_code == 200
        status_body = status.json()
        if status_body["status"] == "completed":
            break
        time.sleep(0.02)

    assert status_body is not None
    assert status_body["status"] == "completed"
    assert status_body["result_url"].startswith("/qr/")
    assert status_body["download_url"].startswith("/qr/")
    with SessionLocal() as db:
        job = db.get(GenerationJob, body["id"])
        assert job is not None
        assert job.result_path is not None
        assert job.result_path.endswith(".jpg")


def test_create_job_returns_processing_status_immediately(monkeypatch) -> None:
    _reset_db()

    monkeypatch.setattr("app.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    assert created.json()["status"] == "processing"


def test_create_job_uses_saved_model_setting(monkeypatch) -> None:
    _reset_db()
    captured: dict[str, str] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured["model"] = model
        return b"generated-image-bytes"

    monkeypatch.setattr("app.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    updated = client.put("/api/settings/model", json={"model_name": "openai/gpt-5-image"})
    assert updated.status_code == 200

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    assert created.json()["status"] == "processing"

    for _ in range(30):
        if "model" in captured:
            break
        time.sleep(0.02)
    assert captured["model"] == "openai/gpt-5-image"


@pytest.mark.parametrize("legacy_model", [LEGACY_MODEL_NAME, LEGACY_OPENAI_MODEL_NAME, "openai/gpt-5-image-mini"])
def test_create_job_falls_back_from_legacy_model(monkeypatch, legacy_model: str) -> None:
    _reset_db()
    captured: dict[str, str] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured["model"] = model
        return b"generated-image-bytes"

    monkeypatch.setattr("app.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    updated = client.put("/api/settings/model", json={"model_name": legacy_model})
    assert updated.status_code == 200

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    assert created.json()["status"] == "processing"

    for _ in range(30):
        if "model" in captured:
            break
        time.sleep(0.02)
    assert captured["model"] == DEFAULT_MODEL_NAME


def test_create_job_removes_source_photo_after_processing(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    source_dir, _ = _patch_storage_dirs(monkeypatch, tmp_path)

    monkeypatch.setattr("app.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    job_id = created.json()["id"]

    for _ in range(30):
        status = client.get(f"/api/jobs/{job_id}")
        assert status.status_code == 200
        if status.json()["status"] == "completed":
            break
        time.sleep(0.02)

    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        assert job is not None
        assert job.source_path is None

    assert list(source_dir.iterdir()) == []


def test_create_job_removes_results_older_than_retention_days(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    _, result_dir = _patch_storage_dirs(monkeypatch, tmp_path)

    monkeypatch.setenv("RESULT_RETENTION_DAYS", "7")

    stale = result_dir / "old-stale.jpg"
    stale.write_bytes(b"stale")
    stale_timestamp = time.time() - (8 * 24 * 60 * 60)
    os.utime(stale, (stale_timestamp, stale_timestamp))

    fresh = result_dir / "old-fresh.jpg"
    fresh.write_bytes(b"fresh")
    fresh_timestamp = time.time() - (2 * 24 * 60 * 60)
    os.utime(fresh, (fresh_timestamp, fresh_timestamp))

    monkeypatch.setattr("app.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    job_id = created.json()["id"]

    for _ in range(30):
        status = client.get(f"/api/jobs/{job_id}")
        assert status.status_code == 200
        if status.json()["status"] == "completed":
            break
        time.sleep(0.02)

    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        assert job is not None
        assert job.result_path is not None
        newest_result_path = Path(job.result_path)

    result_files = list(result_dir.iterdir())
    result_names = {path.name for path in result_files}
    assert "old-stale.jpg" not in result_names
    assert "old-fresh.jpg" in result_names
    assert newest_result_path.name in result_names


def test_create_job_keeps_all_recent_results_within_retention_days(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    _, result_dir = _patch_storage_dirs(monkeypatch, tmp_path)

    monkeypatch.setenv("RESULT_RETENTION_DAYS", "7")

    now = time.time()
    for idx in range(12):
        existing = result_dir / f"recent-{idx:02d}.jpg"
        existing.write_bytes(f"recent-{idx}".encode("utf-8"))
        timestamp = now - (12 - idx) * 60
        os.utime(existing, (timestamp, timestamp))

    monkeypatch.setattr("app.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    job_id = created.json()["id"]

    for _ in range(30):
        status = client.get(f"/api/jobs/{job_id}")
        assert status.status_code == 200
        if status.json()["status"] == "completed":
            break
        time.sleep(0.02)

    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        assert job is not None
        assert job.result_path is not None
        newest_result_path = Path(job.result_path)

    result_files = list(result_dir.iterdir())
    assert len(result_files) == 13
    result_names = {path.name for path in result_files}
    assert newest_result_path.name in result_names
    for idx in range(12):
        assert f"recent-{idx:02d}.jpg" in result_names
