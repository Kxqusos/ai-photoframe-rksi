import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_BASE_DIR = Path(__file__).resolve().parents[1]


def _resolve_database_url(raw_url: str | None) -> str:
    if not raw_url:
        return f"sqlite:///{(_BASE_DIR / 'photoframe.db').resolve().as_posix()}"

    sqlite_prefixes = ("sqlite:///", "sqlite+pysqlite:///")
    for prefix in sqlite_prefixes:
        if not raw_url.startswith(prefix):
            continue

        path_and_query = raw_url[len(prefix) :]
        path_part, has_query, query_string = path_and_query.partition("?")

        if path_part in {":memory:", ""} or path_part.startswith("/") or path_part.startswith("file:"):
            return raw_url

        resolved = (_BASE_DIR / path_part).resolve().as_posix()
        normalized = f"{prefix}{resolved}"
        if has_query:
            normalized = f"{normalized}?{query_string}"
        return normalized

    return raw_url


DATABASE_URL = _resolve_database_url(os.getenv("DATABASE_URL"))

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_generation_jobs_qr_hash()


def _migrate_generation_jobs_qr_hash() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        table_exists = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='generation_jobs'")
        ).fetchone()
        if not table_exists:
            return

        columns = connection.execute(text("PRAGMA table_info(generation_jobs)")).fetchall()
        column_names = {str(row[1]) for row in columns}
        if "qr_hash" not in column_names:
            connection.execute(text("ALTER TABLE generation_jobs ADD COLUMN qr_hash VARCHAR(64)"))

        connection.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_generation_jobs_qr_hash ON generation_jobs (qr_hash)")
        )
