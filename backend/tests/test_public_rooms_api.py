from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import Room


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_list_public_rooms_returns_only_active_rooms() -> None:
    _reset_db()
    client = TestClient(app)

    with SessionLocal() as db:
        db.add_all(
            [
                Room(slug="main", name="Main", model_name="openai/gpt-5-image", is_active=True),
                Room(slug="room-a", name="Room A", model_name="openai/gpt-5-image", is_active=True),
                Room(slug="room-b", name="Room B", model_name="openai/gpt-5-image", is_active=False),
            ]
        )
        db.commit()

    response = client.get("/api/rooms")
    assert response.status_code == 200

    body = response.json()
    assert [row["slug"] for row in body] == ["main", "room-a"]
    assert set(body[0].keys()) == {"id", "slug", "name"}
