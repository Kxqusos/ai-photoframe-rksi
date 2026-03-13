from fastapi import APIRouter

from photoframe_backend.api.http.dependencies import DbSession
from photoframe_backend.api.http.schemas.public import PublicRoomOut
from photoframe_backend.infrastructure.db.models import Room

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[PublicRoomOut])
def list_public_rooms(db: DbSession) -> list[Room]:
    return db.query(Room).filter(Room.is_active.is_(True)).order_by(Room.id.asc()).all()


__all__ = ["router"]
