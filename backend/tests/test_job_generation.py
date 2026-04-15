import os
import re
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fastapi.staticfiles import StaticFiles

from photoframe_backend.infrastructure.db.base import Base
from photoframe_backend.infrastructure.db.session import SessionLocal, engine
from photoframe_backend.application.services.job_runtime import DEFAULT_MODEL_NAME, LEGACY_MODEL_NAME, LEGACY_OPENAI_MODEL_NAME
from photoframe_backend.main import app
from photoframe_backend.infrastructure.db.models import GenerationJob, Room


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
    monkeypatch.setattr("photoframe_backend.application.services.job_runtime.SOURCE_DIR", source_dir)
    monkeypatch.setattr("photoframe_backend.application.services.job_runtime.RESULT_DIR", result_dir)
    return source_dir, result_dir


def test_gallery_results_are_served_from_same_storage_root_as_media_mount() -> None:
    import photoframe_backend.application.services.job_runtime as job_runtime

    media_route = next(route for route in app.routes if getattr(route, "path", None) == "/media")
    assert isinstance(media_route.app, StaticFiles)
    assert job_runtime.STORAGE_ROOT == Path(media_route.app.directory)


def test_sync_legacy_storage_copies_missing_gallery_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import photoframe_backend.application.services.job_runtime as job_runtime

    storage_root = tmp_path / "storage"
    result_dir = storage_root / "results"
    legacy_root = tmp_path / "legacy-storage"
    legacy_result_dir = legacy_root / "results"

    room_dir = legacy_result_dir / "room-ph000000"
    room_dir.mkdir(parents=True, exist_ok=True)
    legacy_file = room_dir / "job-3.jpg"
    legacy_file.write_bytes(b"legacy-image")

    monkeypatch.setattr(job_runtime, "STORAGE_ROOT", storage_root)
    monkeypatch.setattr(job_runtime, "RESULT_DIR", result_dir)
    monkeypatch.setattr(job_runtime, "LEGACY_STORAGE_ROOT", legacy_root)

    job_runtime.sync_legacy_storage()

    copied = result_dir / "room-ph000000" / "job-3.jpg"
    assert copied.read_bytes() == b"legacy-image"


def test_create_job_and_get_completed_result(monkeypatch) -> None:
    _reset_db()

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        assert model
        assert prompt
        assert image_bytes == b"source-image"
        return b"generated-image-bytes"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    files = {"photo": ("photo.jpg", b"source-image", "image/jpeg")}
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


def test_job_service_rejects_missing_room(monkeypatch) -> None:
    from photoframe_backend.application.services.job_service import JobService
    from photoframe_backend.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
    from photoframe_backend.infrastructure.db.repositories.prompts import SqlAlchemyPromptRepository
    from photoframe_backend.infrastructure.db.repositories.rooms import SqlAlchemyRoomRepository

    _reset_db()
    client = TestClient(app)
    prompt_id = _create_prompt(client)

    with SessionLocal() as db:
        service = JobService(
            room_repository=SqlAlchemyRoomRepository(db),
            prompt_repository=SqlAlchemyPromptRepository(db),
            job_repository=SqlAlchemyJobRepository(db, source_dir=Path("/tmp")),
        )

        try:
            service.create_processing_job(prompt_id=prompt_id, room_slug="zzzzzzzz", source_bytes=b"source-image")
        except ValueError as exc:
            assert str(exc) == "room not found"
        else:
            raise AssertionError("expected missing room failure")


def test_create_job_returns_processing_status_immediately(monkeypatch) -> None:
    _reset_db()

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

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

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)

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


def test_create_job_uses_provider_settings_from_site_even_when_vless_routing_is_disabled(monkeypatch) -> None:
    _reset_db()
    captured: dict[str, str | bool | None] = {}

    def fake_generate_image(
        *,
        model: str,
        prompt: str,
        image_bytes: bytes,
        route_via_proxy: bool = False,
        provider_base_url: str | None = None,
        provider_api_key: str | None = None,
    ) -> bytes:
        captured["model"] = model
        captured["route_via_proxy"] = route_via_proxy
        captured["provider_base_url"] = provider_base_url
        captured["provider_api_key"] = provider_api_key
        return b"generated-image-bytes"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.image_generation.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    provider_saved = client.put(
        "/api/admin/llm-routing/provider",
        json={
            "provider_base_url": "https://embedded.pups-labs.ru/",
            "provider_api_key": "sk-test-key",
            "custom_providers": [{"base_url": "https://embedded.pups-labs.ru/", "api_key": "sk-test-key"}],
        },
    )
    assert provider_saved.status_code == 401

    from photoframe_backend.api.http.security import settings as auth_settings

    auth_settings.auth.admin_username = "admin"
    auth_settings.auth.admin_password = "super-secret-password"
    auth_settings.auth.jwt_secret = "test-jwt-secret-with-at-least-32-bytes"
    auth_settings.auth.jwt_expire_minutes = 60
    login = client.post("/api/admin/auth/login", json={"username": "admin", "password": "super-secret-password"})
    token = login.json()["access_token"]
    provider_saved = client.put(
        "/api/admin/llm-routing/provider",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "provider_base_url": "https://embedded.pups-labs.ru/",
            "provider_api_key": "sk-test-key",
            "custom_providers": [{"base_url": "https://embedded.pups-labs.ru/", "api_key": "sk-test-key"}],
        },
    )
    assert provider_saved.status_code == 200

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202

    for _ in range(30):
        if "provider_base_url" in captured:
            break
        time.sleep(0.02)

    assert captured["route_via_proxy"] is False
    assert captured["provider_base_url"] == "https://embedded.pups-labs.ru/v1"
    assert captured["provider_api_key"] == "sk-test-key"


def test_create_job_retries_generation_until_success(monkeypatch) -> None:
    _reset_db()
    attempts = {"count": 0}

    def flaky_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("OpenRouter request failed (500): Connection error.")
        return b"generated-image-bytes"

    monkeypatch.setattr("photoframe_backend.api.http.routers.jobs._GENERATION_RETRY_DELAY_SECONDS", 0)
    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", flaky_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
        data={"prompt_id": str(prompt_id)},
    )
    assert created.status_code == 202
    job_hash = created.json()["id"]

    status_body: dict[str, str] | None = None
    for _ in range(80):
        status = client.get(f"/api/jobs/hash/{job_hash}")
        assert status.status_code == 200
        status_body = status.json()
        if status_body["status"] == "completed":
            break
        time.sleep(0.02)

    assert attempts["count"] == 3
    assert status_body is not None
    assert status_body["status"] == "completed"


def test_create_job_uses_default_room_model_when_it_differs_from_legacy_setting(monkeypatch) -> None:
    _reset_db()
    captured: dict[str, str] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured["model"] = model
        return b"generated-image-bytes"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    updated = client.put("/api/settings/model", json={"model_name": "openai/gpt-5-image"})
    assert updated.status_code == 200

    with SessionLocal() as db:
        room = db.query(Room).filter(Room.slug == "ph000000").first()
        assert room is not None
        room.model_name = "google/gemini-2.5-flash-image"
        db.add(room)
        db.commit()

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
    assert captured["model"] == "google/gemini-2.5-flash-image"


@pytest.mark.parametrize("legacy_model", [LEGACY_MODEL_NAME, LEGACY_OPENAI_MODEL_NAME, "openai/gpt-5-image-mini"])
def test_create_job_falls_back_from_legacy_model(monkeypatch, legacy_model: str) -> None:
    _reset_db()
    captured: dict[str, str] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured["model"] = model
        return b"generated-image-bytes"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)

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

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
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

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
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

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", lambda **kwargs: b"generated-image-bytes")

    client = TestClient(app)
    prompt_id = _create_prompt(client)

    created = client.post(
        "/api/jobs",
        files={"photo": ("photo.jpg", b"source-image", "image/jpeg")},
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
