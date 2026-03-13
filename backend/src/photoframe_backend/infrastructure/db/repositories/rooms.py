from collections.abc import Sequence

from sqlalchemy.orm import Session

from photoframe_backend.infrastructure.db.models import Room


class SqlAlchemyRoomRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, room_id: int) -> Room | None:
        return self._db.get(Room, room_id)

    def get_by_slug(self, room_slug: str, *, active_only: bool) -> Room | None:
        query = self._db.query(Room).filter(Room.slug == room_slug)
        if active_only:
            query = query.filter(Room.is_active.is_(True))
        return query.first()

    def list_active(self) -> Sequence[Room]:
        return self._db.query(Room).filter(Room.is_active.is_(True)).order_by(Room.id.asc()).all()

    def create_default_room(self, *, slug: str, name: str, model_name: str) -> Room:
        room = Room(slug=slug, name=name, model_name=model_name, is_active=True)
        self._db.add(room)
        self._db.commit()
        self._db.refresh(room)
        return room
