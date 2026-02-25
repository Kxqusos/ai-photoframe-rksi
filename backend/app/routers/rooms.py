from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Room
from app.schemas import PublicRoomOut

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[PublicRoomOut])
def list_public_rooms(db: Session = Depends(get_db)) -> list[Room]:
    return db.query(Room).filter(Room.is_active.is_(True)).order_by(Room.id.asc()).all()
