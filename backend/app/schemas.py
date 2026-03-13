from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.hash_utils import PUBLIC_ID_PATTERN

PublicId = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=PUBLIC_ID_PATTERN)]
RoomName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
ModelName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
PromptName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
PromptDescription = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
PromptText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
MediaUrl = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class RoomCreate(BaseModel):
    slug: PublicId | None = None
    name: RoomName
    model_name: ModelName
    is_active: bool = True


class RoomOut(RoomCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PublicRoomOut(BaseModel):
    id: int
    slug: PublicId
    name: str

    model_config = ConfigDict(from_attributes=True)


class RoomUpdate(BaseModel):
    slug: PublicId | None = None
    name: RoomName
    model_name: ModelName
    is_active: bool


class RoomModelUpdate(BaseModel):
    model_name: ModelName


class RoomPatch(BaseModel):
    slug: PublicId | None = None
    name: RoomName | None = None
    model_name: ModelName | None = None
    is_active: bool | None = None


class PromptCreate(BaseModel):
    name: PromptName
    description: PromptDescription
    prompt: PromptText
    preview_image_url: MediaUrl
    icon_image_url: MediaUrl


class PromptOut(PromptCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ModelSettingIn(BaseModel):
    model_name: ModelName


class ModelSettingOut(BaseModel):
    id: int
    model_name: str

    model_config = ConfigDict(from_attributes=True)


class JobCreated(BaseModel):
    id: PublicId
    status: str


class JobStatusOut(BaseModel):
    id: PublicId
    status: str
    result_url: str | None = None
    download_url: str | None = None
    qr_url: str | None = None
    error_message: str | None = None


class GalleryImageOut(BaseModel):
    name: str
    url: str
    modified_at: float
