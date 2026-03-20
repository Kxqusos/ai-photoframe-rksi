from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from photoframe_backend.api.http.dependencies import DbSession, require_admin
from photoframe_backend.api.http.routers.media import save_prompt_icon, save_prompt_preview
from photoframe_backend.api.http.security import hash_room_password, settings
from photoframe_backend.api.http.schemas.admin import (
    LlmRoutingConfigUpdate,
    LlmRoutingOut,
    LlmRoutingToggle,
    PromptCreate,
    PromptOut,
    RoomCreate,
    RoomPatch,
    RoomModelUpdate,
    RoomOut,
    RoomUpdate,
)
from photoframe_backend.application.services import llm_routing
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

    room = Room(
        **payload.model_dump(exclude={"slug", "password"}),
        slug=slug,
        room_password_hash=hash_room_password(payload.password),
    )
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
    if payload.password:
        room.room_password_hash = hash_room_password(payload.password)
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
    if payload.password:
        room.room_password_hash = hash_room_password(payload.password)

    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: DbSession) -> Response:
    room = _get_room_or_404(db, room_id)

    db.query(GenerationJob).filter(GenerationJob.room_id == room_id).delete(synchronize_session=False)
    db.query(Prompt).filter(Prompt.room_id == room_id).delete(synchronize_session=False)
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


@router.put("/rooms/{room_id}/prompts/{prompt_id}", response_model=PromptOut)
def update_room_prompt(room_id: int, prompt_id: int, payload: PromptCreate, db: DbSession) -> Prompt:
    _get_room_or_404(db, room_id)
    prompt = db.get(Prompt, prompt_id)
    if prompt is None or prompt.room_id != room_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="prompt not found")

    prompt.name = payload.name
    prompt.description = payload.description
    prompt.prompt = payload.prompt
    prompt.preview_image_url = payload.preview_image_url
    prompt.icon_image_url = payload.icon_image_url
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


@router.get("/llm-routing", response_model=LlmRoutingOut)
def get_llm_routing(db: DbSession) -> LlmRoutingOut:
    setting = llm_routing.get_or_create_llm_routing_setting(db)
    return LlmRoutingOut.from_model(setting)


@router.put("/llm-routing/config", response_model=LlmRoutingOut)
def update_llm_routing_config(payload: LlmRoutingConfigUpdate, db: DbSession) -> LlmRoutingOut:
    setting = llm_routing.save_vless_uri(db, payload.vless_uri)
    return LlmRoutingOut.from_model(setting)


@router.post("/llm-routing/test", response_model=LlmRoutingOut)
def test_llm_routing(db: DbSession) -> LlmRoutingOut:
    setting = llm_routing.test_routing(db)
    return LlmRoutingOut.from_model(setting)


@router.post("/llm-routing/toggle", response_model=LlmRoutingOut)
def toggle_llm_routing(payload: LlmRoutingToggle, db: DbSession) -> LlmRoutingOut:
    setting = llm_routing.set_routing_enabled(db, payload.enabled)
    return LlmRoutingOut.from_model(setting)


__all__ = ["router"]
