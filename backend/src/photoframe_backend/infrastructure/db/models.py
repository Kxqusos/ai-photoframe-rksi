import json
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from photoframe_backend.infrastructure.db.base import Base
from photoframe_backend.infrastructure.clients.openrouter_client import OPENROUTER_BASE_URL


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    room_password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")


class ModelSetting(Base):
    __tablename__ = "model_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)


class LlmRoutingSetting(Base):
    __tablename__ = "llm_routing_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="disabled")
    vless_uri: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider_base_url: Mapped[str] = mapped_column(Text, nullable=False, default=OPENROUTER_BASE_URL)
    provider_api_key: Mapped[str] = mapped_column(Text, nullable=False, default="")
    custom_providers_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    last_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    @property
    def custom_providers(self) -> list[dict[str, str]]:
        try:
            payload = json.loads(self.custom_providers_json)
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        providers: list[dict[str, str]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            base_url = item.get("base_url")
            api_key = item.get("api_key")
            if isinstance(base_url, str) and isinstance(api_key, str):
                providers.append({"base_url": base_url, "api_key": api_key})
        return providers


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    preview_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    icon_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False, default=1, index=True)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False, default=1, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    qr_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    source_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
