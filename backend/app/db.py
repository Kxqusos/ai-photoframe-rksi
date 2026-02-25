import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ROOM_ID = 1
DEFAULT_ROOM_SLUG = "main"
DEFAULT_ROOM_NAME = "Main"
DEFAULT_ROOM_MODEL = "openai/gpt-5-image"


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
    _migrate_rooms_schema()
    _migrate_generation_jobs_qr_hash()


def _migrate_rooms_schema() -> None:
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        if "rooms" not in tables:
            return

        _ensure_default_room_exists(connection)
        _migrate_room_id_column(connection, "prompts", "ix_prompts_room_id")
        _migrate_room_id_column(connection, "generation_jobs", "ix_generation_jobs_room_id")


def _ensure_default_room_exists(connection) -> None:
    if DATABASE_URL.startswith("sqlite"):
        connection.execute(
            text(
                """
                INSERT OR IGNORE INTO rooms (id, slug, name, model_name, is_active)
                VALUES (:id, :slug, :name, :model_name, :is_active)
                """
            ),
            {
                "id": DEFAULT_ROOM_ID,
                "slug": DEFAULT_ROOM_SLUG,
                "name": DEFAULT_ROOM_NAME,
                "model_name": DEFAULT_ROOM_MODEL,
                "is_active": 1,
            },
        )
        return

    connection.execute(
        text(
            """
            INSERT INTO rooms (id, slug, name, model_name, is_active)
            VALUES (:id, :slug, :name, :model_name, :is_active)
            ON CONFLICT (slug) DO NOTHING
            """
        ),
        {
            "id": DEFAULT_ROOM_ID,
            "slug": DEFAULT_ROOM_SLUG,
            "name": DEFAULT_ROOM_NAME,
            "model_name": DEFAULT_ROOM_MODEL,
            "is_active": True,
        },
    )


def _migrate_room_id_column(connection, table_name: str, index_name: str) -> None:
    if table_name not in set(inspect(connection).get_table_names()):
        return

    existing_columns = {column["name"] for column in inspect(connection).get_columns(table_name)}
    if "room_id" not in existing_columns:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN room_id INTEGER"))

    connection.execute(
        text(f"UPDATE {table_name} SET room_id = :room_id WHERE room_id IS NULL"),
        {"room_id": DEFAULT_ROOM_ID},
    )
    connection.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} (room_id)"))


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
