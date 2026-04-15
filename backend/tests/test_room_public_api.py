from pathlib import Path
import time
import base64
import hashlib

from fastapi.testclient import TestClient

from photoframe_backend.infrastructure.db.base import Base
from photoframe_backend.infrastructure.db.session import SessionLocal, engine
from photoframe_backend.main import app
from photoframe_backend.infrastructure.db.models import GenerationJob, Prompt, Room


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _hash_room_password(password: str) -> str:
    salt = b"room-access-test-salt"
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def _room_headers(token: str | None = None) -> dict[str, str]:
    return {"X-Room-Access-Token": token} if token else {}


def _get_room_access_token(client: TestClient, room_slug: str, password: str) -> str:
    response = client.post(f"/api/rooms/{room_slug}/access", json={"password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed_rooms_and_prompts() -> dict[str, int]:
    with SessionLocal() as db:
        room_main = Room(
            slug="ph000000",
            name="Main",
            model_name="openai/gpt-5-image",
            is_active=True,
            room_password_hash=_hash_room_password("main-pass"),
        )
        room_a = Room(
            slug="aaaaaaaa",
            name="Room A",
            model_name="openai/gpt-5-image",
            is_active=True,
            room_password_hash=_hash_room_password("room-a-pass"),
        )
        room_b = Room(
            slug="bbbbbbbb",
            name="Room B",
            model_name="google/gemini-2.5-flash-image",
            is_active=True,
            room_password_hash=_hash_room_password("room-b-pass"),
        )
        db.add_all([room_main, room_a, room_b])
        db.commit()
        db.refresh(room_main)
        db.refresh(room_a)
        db.refresh(room_b)

        prompt_a = Prompt(
            name="Style A",
            description="A",
            prompt="Prompt A",
            preview_image_url="/media/previews/a.jpg",
            icon_image_url="/media/icons/a.png",
            room_id=room_a.id,
        )
        prompt_b = Prompt(
            name="Style B",
            description="B",
            prompt="Prompt B",
            preview_image_url="/media/previews/b.jpg",
            icon_image_url="/media/icons/b.png",
            room_id=room_b.id,
        )
        db.add_all([prompt_a, prompt_b])
        db.commit()
        db.refresh(prompt_a)
        db.refresh(prompt_b)

        return {
            "room_a_id": room_a.id,
            "room_b_id": room_b.id,
            "prompt_a_id": prompt_a.id,
            "prompt_b_id": prompt_b.id,
        }


def test_room_prompts_endpoint_returns_only_room_prompts() -> None:
    _reset_db()
    _seed_rooms_and_prompts()
    client = TestClient(app)
    token = _get_room_access_token(client, "aaaaaaaa", "room-a-pass")

    response = client.get("/api/rooms/aaaaaaaa/prompts", headers=_room_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Style A"


def test_room_job_creation_rejects_prompt_from_another_room() -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)
    token = _get_room_access_token(client, "aaaaaaaa", "room-a-pass")

    response = client.post(
        "/api/rooms/aaaaaaaa/jobs",
        headers=_room_headers(token),
        files={"photo": ("photo.jpg", b"photo-bytes", "image/jpeg")},
        data={"prompt_id": str(ids["prompt_b_id"])},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "prompt does not belong to room"


def test_room_gallery_endpoint_returns_only_room_results(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    result_root = tmp_path / "results"
    monkeypatch.setattr("photoframe_backend.application.services.job_runtime.RESULT_DIR", result_root)
    client = TestClient(app)
    token = _get_room_access_token(client, "aaaaaaaa", "room-a-pass")

    room_a_dir = result_root / "room-aaaaaaaa"
    room_b_dir = result_root / "room-bbbbbbbb"
    room_a_dir.mkdir(parents=True, exist_ok=True)
    room_b_dir.mkdir(parents=True, exist_ok=True)

    file_a = room_a_dir / "job-a.jpg"
    file_b = room_b_dir / "job-b.jpg"
    file_a.write_bytes(b"a")
    file_b.write_bytes(b"b")

    with SessionLocal() as db:
        db.add_all(
            [
                GenerationJob(
                    prompt_id=ids["prompt_a_id"],
                    room_id=ids["room_a_id"],
                    status="completed",
                    qr_hash="aaaaaaaa",
                    result_path=str(file_a),
                ),
                GenerationJob(
                    prompt_id=ids["prompt_b_id"],
                    room_id=ids["room_b_id"],
                    status="completed",
                    qr_hash="bbbbbbbb",
                    result_path=str(file_b),
                ),
            ]
        )
        db.commit()

    response = client.get("/api/rooms/aaaaaaaa/jobs/gallery", headers=_room_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "job-a.jpg"


def test_room_hash_endpoint_enforces_room_ownership() -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)

    with SessionLocal() as db:
        db.add(
            GenerationJob(
                prompt_id=ids["prompt_a_id"],
                room_id=ids["room_a_id"],
                status="completed",
                qr_hash="cccccccc",
                result_path="/tmp/job-c.jpg",
            )
        )
        db.commit()

    token = _get_room_access_token(client, "bbbbbbbb", "room-b-pass")
    response = client.get("/api/rooms/bbbbbbbb/jobs/hash/cccccccc", headers=_room_headers(token))
    assert response.status_code == 404


def test_room_hash_websocket_streams_status_updates_for_room_job(monkeypatch) -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)
    token = _get_room_access_token(client, "aaaaaaaa", "room-a-pass")
    monkeypatch.setattr("photoframe_backend.api.http.routers.jobs._JOB_STATUS_WS_POLL_SECONDS", 0.01)

    with SessionLocal() as db:
        job = GenerationJob(
            prompt_id=ids["prompt_a_id"],
            room_id=ids["room_a_id"],
            status="processing",
            qr_hash="strm0001",
            result_path=None,
        )
        db.add(job)
        db.commit()

    with client.websocket_connect(f"/api/rooms/aaaaaaaa/jobs/hash/strm0001/ws?room_access_token={token}") as websocket:
        first = websocket.receive_json()
        assert first["id"] == "strm0001"
        assert first["status"] == "processing"

        with SessionLocal() as db:
            job = db.query(GenerationJob).filter(GenerationJob.qr_hash == "strm0001").first()
            assert job is not None
            job.status = "completed"
            job.result_path = "/tmp/strm0001.jpg"
            db.add(job)
            db.commit()

        second = websocket.receive_json()
        assert second["id"] == "strm0001"
        assert second["status"] == "completed"
        assert second["download_url"] == "/qr/strm0001"


def test_room_job_status_by_id_returns_room_scoped_status() -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)

    with SessionLocal() as db:
        job = GenerationJob(
            prompt_id=ids["prompt_a_id"],
            room_id=ids["room_a_id"],
            status="completed",
            qr_hash="dddddddd",
            result_path="/tmp/job-d.jpg",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

    token_a = _get_room_access_token(client, "aaaaaaaa", "room-a-pass")
    token_b = _get_room_access_token(client, "bbbbbbbb", "room-b-pass")

    response = client.get(f"/api/rooms/aaaaaaaa/jobs/{job_id}", headers=_room_headers(token_a))
    assert response.status_code == 200
    assert response.json()["id"] == "dddddddd"
    assert response.json()["qr_url"] == "/api/jobs/hash/dddddddd/qr"

    wrong_room = client.get(f"/api/rooms/bbbbbbbb/jobs/{job_id}", headers=_room_headers(token_b))
    assert wrong_room.status_code == 404


def test_public_qr_png_endpoint_works_for_completed_room_scoped_job() -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)

    with SessionLocal() as db:
        job = GenerationJob(
            prompt_id=ids["prompt_a_id"],
            room_id=ids["room_a_id"],
            status="completed",
            qr_hash="qrroom01",
            result_path="/tmp/job-room-a.jpg",
        )
        db.add(job)
        db.commit()

    response = client.get("/api/jobs/hash/qrroom01/qr")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_room_job_generation_uses_room_model(monkeypatch) -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    captured_models: list[str] = []

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured_models.append(model)
        return b"generated-image-bytes"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)
    client = TestClient(app)
    token_a = _get_room_access_token(client, "aaaaaaaa", "room-a-pass")
    token_b = _get_room_access_token(client, "bbbbbbbb", "room-b-pass")

    created_a = client.post(
        "/api/rooms/aaaaaaaa/jobs",
        headers=_room_headers(token_a),
        files={"photo": ("photo-a.jpg", b"photo-a", "image/jpeg")},
        data={"prompt_id": str(ids["prompt_a_id"])},
    )
    assert created_a.status_code == 202

    created_b = client.post(
        "/api/rooms/bbbbbbbb/jobs",
        headers=_room_headers(token_b),
        files={"photo": ("photo-b.jpg", b"photo-b", "image/jpeg")},
        data={"prompt_id": str(ids["prompt_b_id"])},
    )
    assert created_b.status_code == 202

    for _ in range(30):
        status_a = client.get(f"/api/rooms/aaaaaaaa/jobs/hash/{created_a.json()['id']}", headers=_room_headers(token_a))
        status_b = client.get(f"/api/rooms/bbbbbbbb/jobs/hash/{created_b.json()['id']}", headers=_room_headers(token_b))
        if status_a.status_code == 200 and status_b.status_code == 200:
            if status_a.json()["status"] == "completed" and status_b.json()["status"] == "completed":
                break
        time.sleep(0.02)

    assert "openai/gpt-5-image" in captured_models
    assert "google/gemini-2.5-flash-image" in captured_models


def test_room_access_endpoint_rejects_wrong_password() -> None:
    _reset_db()
    _seed_rooms_and_prompts()
    client = TestClient(app)

    response = client.post("/api/rooms/aaaaaaaa/access", json={"password": "wrong-pass"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid room password"


def test_room_scoped_public_endpoints_require_room_access_token() -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)

    prompts = client.get("/api/rooms/aaaaaaaa/prompts")
    create_job = client.post(
        "/api/rooms/aaaaaaaa/jobs",
        files={"photo": ("photo.jpg", b"photo-bytes", "image/jpeg")},
        data={"prompt_id": str(ids["prompt_a_id"])},
    )
    gallery = client.get("/api/rooms/aaaaaaaa/jobs/gallery")

    assert prompts.status_code == 401
    assert create_job.status_code == 401
    assert gallery.status_code == 401
