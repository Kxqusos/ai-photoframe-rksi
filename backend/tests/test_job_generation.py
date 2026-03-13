import os
import re
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.job_service import (
    DEFAULT_MODEL_NAME,
    LEGACY_MODEL_NAME,
    LEGACY_OPENAI_MODEL_NAME,
    create_processing_job,
    get_or_create_default_room,
    run_generation_sync,
)
from app.main import app
from app.models import GenerationJob, Prompt, Room
from tests.image_utils import tiny_jpeg_bytes

SOURCE_IMAGE = tiny_jpeg_bytes()


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _configure_admin_credentials(monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    from app.auth import settings

    username = "admin"
    password = "super-secret-password"

    monkeypatch.setattr(settings, "admin_username", username)
    monkeypatch.setattr(settings, "admin_password", password)
    monkeypatch.setattr(settings, "jwt_secret", "test-jwt-secret-with-at-least-32-bytes")
    monkeypatch.setattr(settings, "jwt_expire_minutes", 60)
    return username, password


def _get_admin_headers(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    username, password = _configure_admin_credentials(monkeypatch)
    response = client.post("/api/admin/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_prompt(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> int:
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
        assert image_bytes == SOURCE_IMAGE
        return b"generated-image-bytes"

    monkeypatch.setattr("app.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client, monkeypatch)

    files = {"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")}
    data = {"prompt_id": str(prompt_id)}
    created = client.post("/api/jobs", files=files, data=data)
    assert created.status_code == 202

    body = created.json()
    assert isinstance(body["id"], str)
    assert re.fullmatch(r"[a-z0-9]{8}", body["id"])
    assert body["status"] == "processing"

    status_body: dict[str, str] | None = None
    for _ in range(30):
        status = client.get(f"/api/jobs/hash/{body['id']}")
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
        job = db.query(GenerationJob).filter(GenerationJob.qr_hash == body["id"]).first()
        assert job is not None
        assert job.result_path is not None
        assert job.result_path.endswith(".jpg")


def test_create_job_returns_processing_status_immediately(monkeypatch) -> None:
    _reset_db()

    monkeypatch.setattr("app.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

    client = TestClient(app)
    prompt_id = _create_prompt(client, monkeypatch)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    assert created.json()["status"] == "processing"


def test_create_job_rejects_non_image_upload(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    prompt_id = _create_prompt(client, monkeypatch)

    response = client.post(
        "/api/jobs",
        files={"photo": ("photo.txt", b"hello", "text/plain")},
        data={"prompt_id": str(prompt_id)},
    )

    assert response.status_code == 400


def test_create_job_rejects_oversized_upload(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    prompt_id = _create_prompt(client, monkeypatch)
    monkeypatch.setattr("app.routers.jobs.MAX_UPLOAD_BYTES", 4)

    response = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )

    assert response.status_code == 413


def test_create_job_does_not_leave_processing_row_when_source_write_fails(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    _patch_storage_dirs(monkeypatch, tmp_path)

    client = TestClient(app, raise_server_exceptions=False)
    prompt_id = _create_prompt(client, monkeypatch)

    def raise_disk_full(self, data: bytes) -> int:
        raise OSError("disk full")

    monkeypatch.setattr("app.job_service.Path.write_bytes", raise_disk_full)

    response = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )

    assert response.status_code == 500
    with SessionLocal() as db:
        assert db.query(GenerationJob).count() == 0


def test_run_generation_sync_removes_source_when_prompt_was_deleted(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    source_dir, _ = _patch_storage_dirs(monkeypatch, tmp_path)

    client = TestClient(app)
    prompt_id = _create_prompt(client, monkeypatch)

    with SessionLocal() as db:
        default_room = get_or_create_default_room(db)
        job = create_processing_job(db, prompt_id=prompt_id, room_id=default_room.id, source_bytes=SOURCE_IMAGE)

        prompt = db.get(Prompt, prompt_id)
        assert prompt is not None
        db.delete(prompt)
        db.commit()

        result = run_generation_sync(db, job.id)
        assert result.status == "error"
        assert result.error_message == "prompt not found"
        assert result.source_path is None

    assert list(source_dir.iterdir()) == []


def test_create_job_uses_saved_model_setting(monkeypatch) -> None:
    _reset_db()
    captured: dict[str, str] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured["model"] = model
        return b"generated-image-bytes"

    monkeypatch.setattr("app.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client, monkeypatch)
    headers = _get_admin_headers(client, monkeypatch)

    updated = client.put("/api/settings/model", json={"model_name": "openai/gpt-5-image"}, headers=headers)
    assert updated.status_code == 200

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    assert created.json()["status"] == "processing"

    for _ in range(30):
        if "model" in captured:
            break
        time.sleep(0.02)
    assert captured["model"] == "openai/gpt-5-image"


def test_create_job_uses_default_room_model_when_it_differs_from_legacy_setting(monkeypatch) -> None:
    _reset_db()
    captured: dict[str, str] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured["model"] = model
        return b"generated-image-bytes"

    monkeypatch.setattr("app.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client, monkeypatch)
    headers = _get_admin_headers(client, monkeypatch)

    updated = client.put("/api/settings/model", json={"model_name": "openai/gpt-5-image"}, headers=headers)
    assert updated.status_code == 200

    with SessionLocal() as db:
        room = db.query(Room).filter(Room.slug == "ph000000").first()
        assert room is not None
        room.model_name = "google/gemini-2.5-flash-image"
        db.add(room)
        db.commit()

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    assert created.json()["status"] == "processing"

    for _ in range(30):
        if "model" in captured:
            break
        time.sleep(0.02)
    assert captured["model"] == "google/gemini-2.5-flash-image"


@pytest.mark.parametrize("legacy_model", [LEGACY_MODEL_NAME, LEGACY_OPENAI_MODEL_NAME, "openai/gpt-5-image-mini"])
def test_create_job_falls_back_from_legacy_model(monkeypatch, legacy_model: str) -> None:
    _reset_db()
    captured: dict[str, str] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured["model"] = model
        return b"generated-image-bytes"

    monkeypatch.setattr("app.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client, monkeypatch)
    headers = _get_admin_headers(client, monkeypatch)

    updated = client.put("/api/settings/model", json={"model_name": legacy_model}, headers=headers)
    assert updated.status_code == 200

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
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
    prompt_id = _create_prompt(client, monkeypatch)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    job_hash = created.json()["id"]

    for _ in range(30):
        status = client.get(f"/api/jobs/hash/{job_hash}")
        assert status.status_code == 200
        if status.json()["status"] == "completed":
            break
        time.sleep(0.02)

    with SessionLocal() as db:
        job = db.query(GenerationJob).filter(GenerationJob.qr_hash == job_hash).first()
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
    prompt_id = _create_prompt(client, monkeypatch)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    job_hash = created.json()["id"]

    for _ in range(30):
        status = client.get(f"/api/jobs/hash/{job_hash}")
        assert status.status_code == 200
        if status.json()["status"] == "completed":
            break
        time.sleep(0.02)

    with SessionLocal() as db:
        job = db.query(GenerationJob).filter(GenerationJob.qr_hash == job_hash).first()
        assert job is not None
        assert job.result_path is not None
        newest_result_path = Path(job.result_path)

    result_files = list(result_dir.iterdir())
    result_names = {path.name for path in result_files}
    assert "old-stale.jpg" not in result_names
    assert "old-fresh.jpg" in result_names
    assert newest_result_path.exists()


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
    prompt_id = _create_prompt(client, monkeypatch)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    job_hash = created.json()["id"]

    for _ in range(30):
        status = client.get(f"/api/jobs/hash/{job_hash}")
        assert status.status_code == 200
        if status.json()["status"] == "completed":
            break
        time.sleep(0.02)

    with SessionLocal() as db:
        job = db.query(GenerationJob).filter(GenerationJob.qr_hash == job_hash).first()
        assert job is not None
        assert job.result_path is not None
        newest_result_path = Path(job.result_path)

    result_files = list(result_dir.iterdir())
    assert len(result_files) == 13
    result_names = {path.name for path in result_files}
    assert newest_result_path.exists()
    for idx in range(12):
        assert f"recent-{idx:02d}.jpg" in result_names


def test_gallery_endpoint_lists_result_files_newest_first(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    _, result_dir = _patch_storage_dirs(monkeypatch, tmp_path)
    client = TestClient(app)

    room_dir = result_dir / "room-ph000000"
    room_dir.mkdir(parents=True, exist_ok=True)

    newest = room_dir / "newest.jpg"
    newest.write_bytes(b"new")
    oldest = room_dir / "oldest.png"
    oldest.write_bytes(b"old")
    skipped = room_dir / "note.txt"
    skipped.write_text("skip me", encoding="utf-8")

    now = time.time()
    os.utime(oldest, (now - 100, now - 100))
    os.utime(newest, (now - 10, now - 10))

    response = client.get("/api/jobs/gallery")
    assert response.status_code == 200

    body = response.json()
    assert [item["name"] for item in body] == ["newest.jpg", "oldest.png"]
    assert body[0]["url"] == "/media/results/room-ph000000/newest.jpg"
    assert body[1]["url"] == "/media/results/room-ph000000/oldest.png"


def test_gallery_endpoint_includes_other_image_extensions(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    _, result_dir = _patch_storage_dirs(monkeypatch, tmp_path)
    client = TestClient(app)

    room_dir = result_dir / "room-ph000000"
    room_dir.mkdir(parents=True, exist_ok=True)

    gif_file = room_dir / "photo.gif"
    gif_file.write_bytes(b"GIF89a")

    response = client.get("/api/jobs/gallery")
    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["photo.gif"]
