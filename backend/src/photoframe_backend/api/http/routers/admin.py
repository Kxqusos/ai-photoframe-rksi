from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from photoframe_backend.api.http.dependencies import DbSession, require_admin
from photoframe_backend.api.http.routers.media import save_prompt_icon, save_prompt_preview
from photoframe_backend.api.http.security import settings
from photoframe_backend.api.http.schemas.admin import (
    PromptCreate,
    PromptOut,
    RoomCreate,
    RoomPatch,
    RoomModelUpdate,
    RoomOut,
    RoomUpdate,
)
from photoframe_backend.infrastructure.db.models import GenerationJob, Prompt, Room
from photoframe_backend.shared.public_ids import generate_public_id

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _get_room_or_404(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="room not found")
    return room


def _generate_unique_room_slug(db: Session) -> str:
    while True:
        candidate = generate_public_id()
        exists = db.query(Room.id).filter(Room.slug == candidate).first()
        if exists is None:
            return candidate


@router.get("/rooms", response_model=list[RoomOut])
def list_rooms(db: DbSession) -> list[Room]:
    return db.query(Room).order_by(Room.id.asc()).all()


@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(payload: RoomCreate, db: DbSession) -> Room:
    slug = payload.slug or _generate_unique_room_slug(db)
    existing = db.query(Room).filter(Room.slug == slug).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="room slug already exists")

    room = Room(**payload.model_dump(exclude={"slug"}), slug=slug)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.put("/rooms/{room_id}", response_model=RoomOut)
def update_room(room_id: int, payload: RoomUpdate, db: DbSession) -> Room:
    room = _get_room_or_404(db, room_id)

    if payload.slug is not None:
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


@router.patch("/rooms/{room_id}", response_model=RoomOut)
def patch_room(room_id: int, payload: RoomPatch, db: DbSession) -> Room:
    room = _get_room_or_404(db, room_id)

    if payload.slug is not None:
        duplicate = db.query(Room).filter(Room.slug == payload.slug, Room.id != room_id).first()
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="room slug already exists")
        room.slug = payload.slug
    if payload.name is not None:
        room.name = payload.name
    if payload.model_name is not None:
        room.model_name = payload.model_name
    if payload.is_active is not None:
        room.is_active = payload.is_active

    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: DbSession) -> Response:
    room = _get_room_or_404(db, room_id)

    if room.slug == settings.app.default_public_room_slug:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="default room cannot be deleted")
    if db.query(Prompt.id).filter(Prompt.room_id == room_id).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="room cannot be deleted while prompts exist")
    if db.query(GenerationJob.id).filter(GenerationJob.room_id == room_id).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="room cannot be deleted while generation jobs exist",
        )

    db.delete(room)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/rooms/{room_id}/model", response_model=RoomOut)
def update_room_model(room_id: int, payload: RoomModelUpdate, db: DbSession) -> Room:
    room = _get_room_or_404(db, room_id)
    room.model_name = payload.model_name
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/rooms/{room_id}/prompts", response_model=list[PromptOut])
def list_room_prompts(room_id: int, db: DbSession) -> list[Prompt]:
    _get_room_or_404(db, room_id)
    return db.query(Prompt).filter(Prompt.room_id == room_id).order_by(Prompt.id.asc()).all()


@router.post("/rooms/{room_id}/prompts", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
def create_room_prompt(room_id: int, payload: PromptCreate, db: DbSession) -> Prompt:
    _get_room_or_404(db, room_id)
    prompt = Prompt(**payload.model_dump(), room_id=room_id)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/rooms/{room_id}/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room_prompt(room_id: int, prompt_id: int, db: DbSession) -> Response:
    _get_room_or_404(db, room_id)
    prompt = db.get(Prompt, prompt_id)
    if prompt is None or prompt.room_id != room_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="prompt not found")

    db.delete(prompt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/rooms/{room_id}/media/prompt-preview", status_code=status.HTTP_201_CREATED)
async def upload_room_prompt_preview(room_id: int, file: UploadFile, db: DbSession) -> dict[str, str]:
    _get_room_or_404(db, room_id)
    return {"url": await save_prompt_preview(file, room_id=room_id)}


@router.post("/rooms/{room_id}/media/prompt-icon", status_code=status.HTTP_201_CREATED)
async def upload_room_prompt_icon(room_id: int, file: UploadFile, db: DbSession) -> dict[str, str]:
    _get_room_or_404(db, room_id)
    return {"url": await save_prompt_icon(file, room_id=room_id)}


__all__ = ["router"]
