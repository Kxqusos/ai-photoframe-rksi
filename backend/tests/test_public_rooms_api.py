from fastapi.testclient import TestClient

from photoframe_backend.infrastructure.db.base import Base
from photoframe_backend.infrastructure.db.session import SessionLocal, engine
from photoframe_backend.main import app
from photoframe_backend.infrastructure.db.models import Room


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_list_public_rooms_returns_only_active_rooms() -> None:
    _reset_db()
    client = TestClient(app)

    with SessionLocal() as db:
        db.add_all(
            [
                Room(slug="ph000000", name="Main", model_name="openai/gpt-5-image", is_active=True),
                Room(slug="aaaaaaaa", name="Room A", model_name="openai/gpt-5-image", is_active=True),
                Room(slug="bbbbbbbb", name="Room B", model_name="openai/gpt-5-image", is_active=False),
            ]
        )
        db.commit()

    response = client.get("/api/rooms")
    assert response.status_code == 200

    body = response.json()
    assert [row["slug"] for row in body] == ["ph000000", "aaaaaaaa"]
    assert set(body[0].keys()) == {"id", "slug", "name"}


def test_room_service_creates_default_room_when_missing() -> None:
    from photoframe_backend.application.services.room_service import RoomService
    from photoframe_backend.infrastructure.db.repositories.rooms import SqlAlchemyRoomRepository

    _reset_db()
    with SessionLocal() as db:
        service = RoomService(SqlAlchemyRoomRepository(db))
        room = service.get_or_create_default_room()

        assert room.slug == "ph000000"
        assert room.name == "Main"
        assert room.is_active is True
