import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.hash_utils import DEFAULT_PUBLIC_ID
from app.hash_utils import generate_public_id, is_public_id

_BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ROOM_ID = 1
DEFAULT_ROOM_SLUG = DEFAULT_PUBLIC_ID
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
    if not DATABASE_URL.startswith("sqlite"):
        return
    Base.metadata.create_all(bind=engine)
    _migrate_rooms_schema()
    _migrate_generation_jobs_qr_hash()


def _migrate_rooms_schema() -> None:
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        if "rooms" not in tables:
            return

        _migrate_room_slugs_to_public_ids(connection)
        _ensure_default_room_exists(connection)
        default_room_id = _lookup_default_room_id(connection)
        _migrate_room_id_column(connection, "prompts", "ix_prompts_room_id", default_room_id)
        _migrate_room_id_column(connection, "generation_jobs", "ix_generation_jobs_room_id", default_room_id)


def _lookup_default_room_id(connection) -> int:
    row = connection.execute(text("SELECT id FROM rooms WHERE slug = :slug LIMIT 1"), {"slug": DEFAULT_ROOM_SLUG}).fetchone()
    if row is None:
        raise RuntimeError("default room is missing after bootstrap")
    return int(row[0])


def _ensure_default_room_exists(connection) -> int:
    if DATABASE_URL.startswith("sqlite"):
        connection.execute(
            text(
                """
                INSERT OR IGNORE INTO rooms (slug, name, model_name, is_active)
                VALUES (:slug, :name, :model_name, :is_active)
                """
            ),
            {
                "slug": DEFAULT_ROOM_SLUG,
                "name": DEFAULT_ROOM_NAME,
                "model_name": DEFAULT_ROOM_MODEL,
                "is_active": 1,
            },
        )
        return _lookup_default_room_id(connection)

    connection.execute(
        text(
            """
            INSERT INTO rooms (slug, name, model_name, is_active)
            VALUES (:slug, :name, :model_name, :is_active)
            ON CONFLICT (slug) DO NOTHING
            """
        ),
        {
            "slug": DEFAULT_ROOM_SLUG,
            "name": DEFAULT_ROOM_NAME,
            "model_name": DEFAULT_ROOM_MODEL,
            "is_active": True,
        },
    )
    return _lookup_default_room_id(connection)


def _generate_unique_room_slug(used_slugs: set[str]) -> str:
    while True:
        candidate = generate_public_id()
        if candidate not in used_slugs:
            return candidate


def _migrate_room_slugs_to_public_ids(connection) -> None:
    rows = connection.execute(text("SELECT id, slug FROM rooms ORDER BY id ASC")).fetchall()
    if not rows:
        return

    used_slugs: set[str] = set()
    for row in rows:
        slug = str(row[1] or "").strip().lower()
        if is_public_id(slug):
            used_slugs.add(slug)

    for row in rows:
        room_id = int(row[0])
        current_slug = str(row[1] or "")
        normalized = current_slug.strip().lower()

        if is_public_id(normalized):
            if normalized != current_slug:
                connection.execute(text("UPDATE rooms SET slug = :slug WHERE id = :id"), {"slug": normalized, "id": room_id})
            continue

        if DEFAULT_ROOM_SLUG not in used_slugs and (room_id == DEFAULT_ROOM_ID or normalized == "main"):
            new_slug = DEFAULT_ROOM_SLUG
        else:
            new_slug = _generate_unique_room_slug(used_slugs)

        connection.execute(text("UPDATE rooms SET slug = :slug WHERE id = :id"), {"slug": new_slug, "id": room_id})
        used_slugs.add(new_slug)


def _migrate_room_id_column(connection, table_name: str, index_name: str, default_room_id: int) -> None:
    if table_name not in set(inspect(connection).get_table_names()):
        return

    existing_columns = {column["name"] for column in inspect(connection).get_columns(table_name)}
    if "room_id" not in existing_columns:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN room_id INTEGER"))

    connection.execute(
        text(f"UPDATE {table_name} SET room_id = :room_id WHERE room_id IS NULL"),
        {"room_id": default_room_id},
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
