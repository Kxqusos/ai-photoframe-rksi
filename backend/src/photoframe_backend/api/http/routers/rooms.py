from fastapi import APIRouter, HTTPException

from photoframe_backend.api.http.dependencies import DbSession
from photoframe_backend.api.http.schemas.public import PublicRoomOut, RoomAccessIn, RoomAccessOut
from photoframe_backend.api.http.security import create_room_access_token, verify_room_password
from photoframe_backend.infrastructure.db.models import Room

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[PublicRoomOut])
def list_public_rooms(db: DbSession) -> list[Room]:
    return db.query(Room).filter(Room.is_active.is_(True)).order_by(Room.id.asc()).all()


@router.post("/{room_slug}/access", response_model=RoomAccessOut)
def access_room(room_slug: str, payload: RoomAccessIn, db: DbSession) -> RoomAccessOut:
    room = db.query(Room).filter(Room.slug == room_slug, Room.is_active.is_(True)).first()
    if room is None:
        raise HTTPException(status_code=404, detail="room not found")
    if not room.room_password_hash:
        raise HTTPException(status_code=409, detail="room password is not configured")
    if not verify_room_password(payload.password, room.room_password_hash):
        raise HTTPException(status_code=401, detail="invalid room password")
    return RoomAccessOut(access_token=create_room_access_token(room.slug))


__all__ = ["router"]
