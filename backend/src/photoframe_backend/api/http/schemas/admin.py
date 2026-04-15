from pydantic import BaseModel, ConfigDict

from photoframe_backend.api.http.schemas.public import PublicId


class RoomCreate(BaseModel):
    slug: PublicId | None = None
    name: str
    model_name: str
    is_active: bool = True
    password: str


class RoomOut(BaseModel):
    id: int
    slug: PublicId
    name: str
    model_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RoomUpdate(BaseModel):
    slug: PublicId | None = None
    name: str
    model_name: str
    is_active: bool
    password: str | None = None


class RoomPatch(BaseModel):
    slug: PublicId | None = None
    name: str | None = None
    model_name: str | None = None
    is_active: bool | None = None
    password: str | None = None


class RoomModelUpdate(BaseModel):
    model_name: str


class CustomProvider(BaseModel):
    base_url: str
    api_key: str


class LlmRoutingConfigUpdate(BaseModel):
    vless_uri: str


class LlmProviderConfigUpdate(BaseModel):
    provider_base_url: str = ""
    provider_api_key: str = ""
    custom_providers: list[CustomProvider] = []


class LlmRoutingToggle(BaseModel):
    enabled: bool


class LlmRoutingOut(BaseModel):
    enabled: bool
    status: str
    vless_uri: str
    provider_base_url: str
    provider_api_key: str
    custom_providers: list[CustomProvider]
    last_error: str | None
    last_checked_at: str | None
    last_applied_at: str | None

    @classmethod
    def from_model(cls, model) -> "LlmRoutingOut":
        return cls(
            enabled=model.enabled,
            status=model.status,
            vless_uri=model.vless_uri,
            provider_base_url=model.provider_base_url,
            provider_api_key=model.provider_api_key,
            custom_providers=model.custom_providers,
            last_error=model.last_error,
            last_checked_at=model.last_checked_at.isoformat() if model.last_checked_at else None,
            last_applied_at=model.last_applied_at.isoformat() if model.last_applied_at else None,
        )


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
    "LlmRoutingConfigUpdate",
    "LlmProviderConfigUpdate",
    "LlmRoutingOut",
    "LlmRoutingToggle",
    "PromptCreate",
    "PromptOut",
    "RoomCreate",
    "RoomPatch",
    "RoomModelUpdate",
    "RoomOut",
    "RoomUpdate",
]
