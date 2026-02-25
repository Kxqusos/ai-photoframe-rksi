from pathlib import Path

from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import GenerationJob, Prompt, Room


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _seed_rooms_and_prompts() -> dict[str, int]:
    with SessionLocal() as db:
        room_main = Room(slug="main", name="Main", model_name="openai/gpt-5-image", is_active=True)
        room_a = Room(slug="room-a", name="Room A", model_name="openai/gpt-5-image", is_active=True)
        room_b = Room(slug="room-b", name="Room B", model_name="openai/gpt-5-image", is_active=True)
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

    response = client.get("/api/rooms/room-a/prompts")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Style A"


def test_room_job_creation_rejects_prompt_from_another_room() -> None:
    _reset_db()
    ids = _seed_rooms_and_prompts()
    client = TestClient(app)

    response = client.post(
        "/api/rooms/room-a/jobs",
        files={"photo": ("photo.jpg", b"photo-bytes", "image/jpeg")},
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

    room_a_dir = result_root / "room-room-a"
    room_b_dir = result_root / "room-room-b"
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
                    qr_hash="aaaaaaaaaaaaaaaa",
                    result_path=str(file_a),
                ),
                GenerationJob(
                    prompt_id=ids["prompt_b_id"],
                    room_id=ids["room_b_id"],
                    status="completed",
                    qr_hash="bbbbbbbbbbbbbbbb",
                    result_path=str(file_b),
                ),
            ]
        )
        db.commit()

    response = client.get("/api/rooms/room-a/jobs/gallery")

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
                qr_hash="cccccccccccccccc",
                result_path="/tmp/job-c.jpg",
            )
        )
        db.commit()

    response = client.get("/api/rooms/room-b/jobs/hash/cccccccccccccccc")
    assert response.status_code == 404
