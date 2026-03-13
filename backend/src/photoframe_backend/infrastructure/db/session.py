import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from photoframe_backend.infrastructure.settings.runtime import load_settings
from photoframe_backend.shared.constants import BACKEND_DIR


def _resolve_database_url(raw_url: str | None) -> str:
    if not raw_url:
        return load_settings(allow_test_defaults=True).database_url

    sqlite_prefixes = ("sqlite:///", "sqlite+pysqlite:///")
    for prefix in sqlite_prefixes:
        if not raw_url.startswith(prefix):
            continue

        path_and_query = raw_url[len(prefix) :]
        path_part, has_query, query_string = path_and_query.partition("?")

        if path_part in {":memory:", ""} or path_part.startswith("/") or path_part.startswith("file:"):
            return raw_url

        resolved = (Path(BACKEND_DIR) / path_part).resolve().as_posix()
        normalized = f"{prefix}{resolved}"
        if has_query:
            normalized = f"{normalized}?{query_string}"
        return normalized

    return raw_url


def build_engine(database_url: str | None = None):
    resolved_url = _resolve_database_url(database_url or os.getenv("DATABASE_URL"))
    connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
    return create_engine(resolved_url, connect_args=connect_args)


def build_session_local(bind):
    return sessionmaker(autocommit=False, autoflush=False, bind=bind)


DATABASE_URL = _resolve_database_url(os.getenv("DATABASE_URL"))
engine = build_engine(DATABASE_URL)
SessionLocal = build_session_local(engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
