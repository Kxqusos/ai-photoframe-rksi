from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db import get_db
from app.models import Prompt, Room
from app.routers.media import save_prompt_icon, save_prompt_preview
from app.schemas import PromptCreate, PromptOut, RoomCreate, RoomModelUpdate, RoomOut, RoomUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _get_room_or_404(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="room not found")
    return room


@router.get("/rooms", response_model=list[RoomOut])
def list_rooms(db: Session = Depends(get_db)) -> list[Room]:
    return db.query(Room).order_by(Room.id.asc()).all()


@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)) -> Room:
    existing = db.query(Room).filter(Room.slug == payload.slug).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="room slug already exists")

    room = Room(**payload.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.put("/rooms/{room_id}", response_model=RoomOut)
def update_room(room_id: int, payload: RoomUpdate, db: Session = Depends(get_db)) -> Room:
    room = _get_room_or_404(db, room_id)
    duplicate = db.query(Room).filter(Room.slug == payload.slug, Room.id != room_id).first()
    if duplicate is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="room slug already exists")

    room.slug = payload.slug
    room.name = payload.name
    room.model_name = payload.model_name
    room.is_active = payload.is_active
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.put("/rooms/{room_id}/model", response_model=RoomOut)
def update_room_model(room_id: int, payload: RoomModelUpdate, db: Session = Depends(get_db)) -> Room:
    room = _get_room_or_404(db, room_id)
    room.model_name = payload.model_name
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/rooms/{room_id}/prompts", response_model=list[PromptOut])
def list_room_prompts(room_id: int, db: Session = Depends(get_db)) -> list[Prompt]:
    _get_room_or_404(db, room_id)
    return db.query(Prompt).filter(Prompt.room_id == room_id).order_by(Prompt.id.asc()).all()


@router.post("/rooms/{room_id}/prompts", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
def create_room_prompt(room_id: int, payload: PromptCreate, db: Session = Depends(get_db)) -> Prompt:
    _get_room_or_404(db, room_id)
    prompt = Prompt(**payload.model_dump(), room_id=room_id)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/rooms/{room_id}/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room_prompt(room_id: int, prompt_id: int, db: Session = Depends(get_db)) -> Response:
    _get_room_or_404(db, room_id)
    prompt = db.get(Prompt, prompt_id)
    if prompt is None or prompt.room_id != room_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="prompt not found")

    db.delete(prompt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/rooms/{room_id}/media/prompt-preview", status_code=status.HTTP_201_CREATED)
async def upload_room_prompt_preview(room_id: int, file: UploadFile, db: Session = Depends(get_db)) -> dict[str, str]:
    _get_room_or_404(db, room_id)
    return {"url": await save_prompt_preview(file, room_id=room_id)}


@router.post("/rooms/{room_id}/media/prompt-icon", status_code=status.HTTP_201_CREATED)
async def upload_room_prompt_icon(room_id: int, file: UploadFile, db: Session = Depends(get_db)) -> dict[str, str]:
    _get_room_or_404(db, room_id)
    return {"url": await save_prompt_icon(file, room_id=room_id)}
