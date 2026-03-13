from fastapi import APIRouter, HTTPException, Response, status

from photoframe_backend.api.http.dependencies import DbSession, PublicIdPath
from photoframe_backend.api.http.schemas.admin import PromptCreate, PromptOut
from photoframe_backend.application.services.job_runtime import get_or_create_default_room, get_room_by_slug
from photoframe_backend.infrastructure.db.models import Prompt

router = APIRouter(prefix="/api/prompts", tags=["prompts"])
room_router = APIRouter(prefix="/api/rooms/{room_slug}/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptOut])
def list_prompts(db: DbSession) -> list[Prompt]:
    default_room = get_or_create_default_room(db)
    return db.query(Prompt).filter(Prompt.room_id == default_room.id).order_by(Prompt.id.asc()).all()


@room_router.get("", response_model=list[PromptOut])
def list_room_prompts(room_slug: PublicIdPath, db: DbSession) -> list[Prompt]:
    room = get_room_by_slug(db, room_slug, active_only=True)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="room not found")
    return db.query(Prompt).filter(Prompt.room_id == room.id).order_by(Prompt.id.asc()).all()


@router.post("", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
def create_prompt(payload: PromptCreate, db: DbSession) -> Prompt:
    default_room = get_or_create_default_room(db)
    row = Prompt(**payload.model_dump(), room_id=default_room.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: int, db: DbSession) -> Response:
    default_room = get_or_create_default_room(db)
    row = db.get(Prompt, prompt_id)
    if row is None or row.room_id != default_room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["room_router", "router"]
