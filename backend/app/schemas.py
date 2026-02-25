from pydantic import BaseModel, ConfigDict


class RoomCreate(BaseModel):
    slug: str
    name: str
    model_name: str
    is_active: bool = True


class RoomOut(RoomCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RoomUpdate(BaseModel):
    slug: str
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


class ModelSettingIn(BaseModel):
    model_name: str


class ModelSettingOut(BaseModel):
    id: int
    model_name: str

    model_config = ConfigDict(from_attributes=True)


class JobCreated(BaseModel):
    id: int
    status: str


class JobStatusOut(BaseModel):
    id: int
    status: str
    result_url: str | None = None
    download_url: str | None = None
    qr_url: str | None = None
    error_message: str | None = None


class GalleryImageOut(BaseModel):
    name: str
    url: str
    modified_at: float
