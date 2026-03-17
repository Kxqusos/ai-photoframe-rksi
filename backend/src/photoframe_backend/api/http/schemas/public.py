from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from photoframe_backend.shared.public_ids import PUBLIC_ID_PATTERN

PublicId = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=PUBLIC_ID_PATTERN)]


class PublicRoomOut(BaseModel):
    id: int
    slug: PublicId
    name: str

    model_config = ConfigDict(from_attributes=True)


class ModelSettingIn(BaseModel):
    model_name: str


class RoomAccessIn(BaseModel):
    password: str


class RoomAccessOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


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


__all__ = [
    "GalleryImageOut",
    "JobCreated",
    "JobStatusOut",
    "ModelSettingIn",
    "ModelSettingOut",
    "PublicId",
    "RoomAccessIn",
    "RoomAccessOut",
    "PublicRoomOut",
]
