from pathlib import Path
import time

from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import GenerationJob, Prompt, Room
from tests.image_utils import tiny_jpeg_bytes

SOURCE_IMAGE = tiny_jpeg_bytes()


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _seed_rooms_and_prompts() -> dict[str, int]:
    with SessionLocal() as db:
        room_main = Room(slug="ph000000", name="Main", model_name="openai/gpt-5-image", is_active=True)
        room_a = Room(slug="aaaaaaaa", name="Room A", model_name="openai/gpt-5-image", is_active=True)
        room_b = Room(slug="bbbbbbbb", name="Room B", model_name="google/gemini-2.5-flash-image", is_active=True)
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

    response = client.get("/api/rooms/aaaaaaaa/prompts")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Style A"


def test_room_prompts_endpoint_returns_404_for_inactive_room() -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)

    with SessionLocal() as db:
        room = db.get(Room, ids["room_a_id"])
        assert room is not None
        room.is_active = False
        db.add(room)
        db.commit()

    response = client.get("/api/rooms/aaaaaaaa/prompts")
    assert response.status_code == 404


def test_room_prompts_endpoint_rejects_invalid_slug() -> None:
    _reset_db()
    _seed_rooms_and_prompts()
    client = TestClient(app)

    response = client.get("/api/rooms/not-valid/prompts")
    assert response.status_code == 422


def test_room_job_creation_rejects_prompt_from_another_room() -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)

    response = client.post(
        "/api/rooms/aaaaaaaa/jobs",
        files={"photo": ("photo.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(ids["prompt_b_id"])},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "prompt does not belong to room"


def test_room_gallery_endpoint_returns_only_room_results(monkeypatch, tmp_path: Path) -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    result_root = tmp_path / "results"
    monkeypatch.setattr("app.job_service.RESULT_DIR", result_root)
    client = TestClient(app)

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

    response = client.get("/api/rooms/aaaaaaaa/jobs/gallery")

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

    response = client.get("/api/rooms/bbbbbbbb/jobs/hash/cccccccc")
    assert response.status_code == 404


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

    response = client.get(f"/api/rooms/aaaaaaaa/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["id"] == "dddddddd"
    assert response.json()["qr_url"] == "/api/rooms/aaaaaaaa/jobs/hash/dddddddd/qr"

    wrong_room = client.get(f"/api/rooms/bbbbbbbb/jobs/{job_id}")
    assert wrong_room.status_code == 404


def test_room_job_generation_uses_room_model(monkeypatch) -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    captured_models: list[str] = []

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured_models.append(model)
        return b"generated-image-bytes"

    monkeypatch.setattr("app.openrouter_client.generate_image", fake_generate_image)
    client = TestClient(app)

    created_a = client.post(
        "/api/rooms/aaaaaaaa/jobs",
        files={"photo": ("photo-a.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(ids["prompt_a_id"])},
    )
    assert created_a.status_code == 202

    created_b = client.post(
        "/api/rooms/bbbbbbbb/jobs",
        files={"photo": ("photo-b.jpg", SOURCE_IMAGE, "image/jpeg")},
        data={"prompt_id": str(ids["prompt_b_id"])},
    )
    assert created_b.status_code == 202

    for _ in range(30):
        status_a = client.get(f"/api/rooms/aaaaaaaa/jobs/hash/{created_a.json()['id']}")
        status_b = client.get(f"/api/rooms/bbbbbbbb/jobs/hash/{created_b.json()['id']}")
        if status_a.status_code == 200 and status_b.status_code == 200:
            if status_a.json()["status"] == "completed" and status_b.json()["status"] == "completed":
                break
        time.sleep(0.02)

    assert "openai/gpt-5-image" in captured_models
    assert "google/gemini-2.5-flash-image" in captured_models
