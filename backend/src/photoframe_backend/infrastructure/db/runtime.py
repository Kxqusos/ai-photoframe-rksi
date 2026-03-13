from sqlalchemy import create_engine, text

from photoframe_backend.infrastructure.db.base import Base
from photoframe_backend.infrastructure.db.bootstrap import init_db as init_db_impl
from photoframe_backend.infrastructure.db.session import (
    DATABASE_URL,
    SessionLocal,
    _resolve_database_url,
    build_engine,
    get_db,
)
from photoframe_backend.shared.public_ids import DEFAULT_PUBLIC_ID, generate_public_id, is_public_id

DEFAULT_ROOM_ID = 1
DEFAULT_ROOM_SLUG = DEFAULT_PUBLIC_ID
engine = build_engine(DATABASE_URL)


def init_db() -> None:
    init_db_impl(
        metadata=Base.metadata,
        engine=engine,
        database_url=DATABASE_URL,
        default_room_slug=DEFAULT_ROOM_SLUG,
        generate_public_id=generate_public_id,
        is_public_id=is_public_id,
    )


__all__ = [
    "Base",
    "DATABASE_URL",
    "DEFAULT_ROOM_ID",
    "DEFAULT_ROOM_SLUG",
    "SessionLocal",
    "_resolve_database_url",
    "build_engine",
    "create_engine",
    "engine",
    "get_db",
    "init_db",
    "text",
]
