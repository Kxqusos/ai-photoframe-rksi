from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ModelSetting(Base):
    __tablename__ = "model_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    preview_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    icon_image_url: Mapped[str] = mapped_column(String(500), nullable=False)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    qr_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    source_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
