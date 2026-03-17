from collections.abc import Callable
import base64
import hashlib
import secrets

from sqlalchemy import inspect, text

DEFAULT_ROOM_ID = 1
DEFAULT_ROOM_NAME = "Main"
DEFAULT_ROOM_MODEL = "openai/gpt-5-image"


def _hash_room_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def bootstrap_default_room(*, engine, database_url: str, default_room_slug: str, fallback_room_password: str = "") -> None:
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        if "rooms" not in tables:
            return

        _ensure_default_room_exists(
            connection=connection,
            database_url=database_url,
            default_room_slug=default_room_slug,
            fallback_room_password=fallback_room_password,
        )
        _backfill_default_room_password(
            connection=connection,
            default_room_slug=default_room_slug,
            fallback_room_password=fallback_room_password,
        )
        _sync_room_id_sequence(connection, database_url)


def init_db(
    *,
    metadata,
    engine,
    database_url: str,
    default_room_slug: str,
    fallback_room_password: str = "",
    generate_public_id: Callable[[], str],
    is_public_id: Callable[[str], bool],
) -> None:
    bootstrap_default_room(
        engine=engine,
        database_url=database_url,
        default_room_slug=default_room_slug,
        fallback_room_password=fallback_room_password,
    )


def _migrate_rooms_schema(*, engine, database_url: str, default_room_slug: str, generate_public_id, is_public_id) -> None:
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        if "rooms" not in tables:
            return

        _ensure_default_room_exists(connection=connection, database_url=database_url, default_room_slug=default_room_slug)
        _migrate_room_slugs_to_public_ids(
            connection=connection,
            default_room_slug=default_room_slug,
            generate_public_id=generate_public_id,
            is_public_id=is_public_id,
        )
        _migrate_room_id_column(connection, "prompts", "ix_prompts_room_id")
        _migrate_room_id_column(connection, "generation_jobs", "ix_generation_jobs_room_id")


def _ensure_default_room_exists(*, connection, database_url: str, default_room_slug: str, fallback_room_password: str) -> None:
    password_hash = _hash_room_password(fallback_room_password) if fallback_room_password else ""
    if database_url.startswith("sqlite"):
        connection.execute(
            text(
                """
                INSERT OR IGNORE INTO rooms (id, slug, name, model_name, is_active, room_password_hash)
                VALUES (:id, :slug, :name, :model_name, :is_active, :room_password_hash)
                """
            ),
            {
                "id": DEFAULT_ROOM_ID,
                "slug": default_room_slug,
                "name": DEFAULT_ROOM_NAME,
                "model_name": DEFAULT_ROOM_MODEL,
                "is_active": 1,
                "room_password_hash": password_hash,
            },
        )
        return

    connection.execute(
        text(
            """
            INSERT INTO rooms (id, slug, name, model_name, is_active, room_password_hash)
            VALUES (:id, :slug, :name, :model_name, :is_active, :room_password_hash)
            ON CONFLICT (slug) DO NOTHING
            """
        ),
        {
            "id": DEFAULT_ROOM_ID,
            "slug": default_room_slug,
            "name": DEFAULT_ROOM_NAME,
            "model_name": DEFAULT_ROOM_MODEL,
            "is_active": True,
            "room_password_hash": password_hash,
        },
    )


def _backfill_default_room_password(*, connection, default_room_slug: str, fallback_room_password: str) -> None:
    if not fallback_room_password:
        return
    current_hash = connection.execute(
        text("SELECT room_password_hash FROM rooms WHERE slug = :slug"),
        {"slug": default_room_slug},
    ).scalar_one_or_none()
    if current_hash:
        return
    connection.execute(
        text("UPDATE rooms SET room_password_hash = :password_hash WHERE slug = :slug"),
        {"slug": default_room_slug, "password_hash": _hash_room_password(fallback_room_password)},
    )


def _sync_room_id_sequence(connection, database_url: str) -> None:
    if database_url.startswith("sqlite"):
        # SQLite rowid tables already continue from max(id) after explicit inserts.
        return

    connection.execute(
        text(
            """
            SELECT setval(
              pg_get_serial_sequence('rooms', 'id'),
              COALESCE((SELECT MAX(id) FROM rooms), 1),
              true
            )
            """
        )
    )


def _generate_unique_room_slug(used_slugs: set[str], generate_public_id: Callable[[], str]) -> str:
    while True:
        candidate = generate_public_id()
        if candidate not in used_slugs:
            return candidate


def _migrate_room_slugs_to_public_ids(*, connection, default_room_slug: str, generate_public_id, is_public_id) -> None:
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

        if default_room_slug not in used_slugs and (room_id == DEFAULT_ROOM_ID or normalized == "main"):
            new_slug = default_room_slug
        else:
            new_slug = _generate_unique_room_slug(used_slugs, generate_public_id)

        connection.execute(text("UPDATE rooms SET slug = :slug WHERE id = :id"), {"slug": new_slug, "id": room_id})
        used_slugs.add(new_slug)


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


def _migrate_generation_jobs_qr_hash(*, engine, database_url: str) -> None:
    if not database_url.startswith("sqlite"):
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
