from pydantic import BaseModel, ConfigDict

from photoframe_backend.api.http.schemas.public import PublicId


class RoomCreate(BaseModel):
    slug: PublicId | None = None
    name: str
    model_name: str
    is_active: bool = True


class RoomOut(RoomCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RoomUpdate(BaseModel):
    slug: PublicId | None = None
    name: str
    model_name: str
    is_active: bool


class RoomModelUpdate(BaseModel):
    model_name: str


class PromptCreate(BaseModel):
    name: str
    description: str
    prompt: str
    preview_image_url: str
    icon_image_url: str


class PromptOut(PromptCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "PromptCreate",
    "PromptOut",
    "RoomCreate",
    "RoomModelUpdate",
    "RoomOut",
    "RoomUpdate",
]
