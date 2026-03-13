from pathlib import Path

import sqlalchemy as sa

from photoframe_backend.infrastructure.db.base import Base
import photoframe_backend.infrastructure.db.models  # noqa: F401
from scripts.check_postgres_ready import check_postgres_ready
from scripts.migrate_sqlite_to_postgres import migrate_sqlite_to_postgres


def _engine_with_sqlite_foreign_keys(database_url: str, create_engine=sa.create_engine) -> sa.Engine:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    @sa.event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _create_legacy_sqlite_db(sqlite_path: Path) -> None:
    engine = sa.create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                CREATE TABLE rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug VARCHAR(120) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    model_name VARCHAR(255) NOT NULL,
                    is_active BOOLEAN NOT NULL
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                CREATE TABLE model_settings (
                    id INTEGER PRIMARY KEY,
                    model_name VARCHAR(255) NOT NULL
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                CREATE TABLE prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(120) NOT NULL,
                    description VARCHAR(500) NOT NULL,
                    prompt TEXT NOT NULL,
                    preview_image_url VARCHAR(500) NOT NULL,
                    icon_image_url VARCHAR(500) NOT NULL,
                    room_id INTEGER NOT NULL
                )
                """
            )
        )
        connection.execute(
            sa.text(
                """
                CREATE TABLE generation_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    room_id INTEGER NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    qr_hash VARCHAR(64),
                    source_path VARCHAR(500),
                    result_path VARCHAR(500),
                    error_message TEXT
                )
                """
            )
        )

        connection.execute(
            sa.text(
                """
                INSERT INTO rooms (id, slug, name, model_name, is_active)
                VALUES (1, 'ph000000', 'Main', 'openai/gpt-5-image', 1),
                       (2, 'room0002', 'Second', 'google/gemini-2.5-flash-image', 0)
                """
            )
        )
        connection.execute(
            sa.text("INSERT INTO model_settings (id, model_name) VALUES (1, 'openai/gpt-5-image')")
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO prompts (id, name, description, prompt, preview_image_url, icon_image_url, room_id)
                VALUES (10, 'Prompt One', 'desc', 'prompt text', '/preview.jpg', '/icon.jpg', 1)
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO generation_jobs (
                    id, prompt_id, room_id, status, qr_hash, source_path, result_path, error_message
                ) VALUES (
                    20, 10, 1, 'completed', 'qr123', '/source.jpg', '/result.jpg', NULL
                )
                """
            )
        )


def test_migrate_sqlite_to_postgres_copies_legacy_rows(tmp_path: Path) -> None:
    source_path = tmp_path / "legacy.db"
    target_path = tmp_path / "target.db"
    target_url = f"sqlite:///{target_path}"
    target_engine = _engine_with_sqlite_foreign_keys(target_url)

    _create_legacy_sqlite_db(source_path)
    Base.metadata.create_all(target_engine)

    migrate_sqlite_to_postgres(source_sqlite_path=source_path, target_database_url=target_url)
    migrate_sqlite_to_postgres(source_sqlite_path=source_path, target_database_url=target_url)

    with target_engine.begin() as connection:
        rooms = connection.execute(sa.text("SELECT id, slug, name, model_name, is_active FROM rooms ORDER BY id")).all()
        prompts = connection.execute(sa.text("SELECT id, room_id, name FROM prompts ORDER BY id")).all()
        jobs = connection.execute(
            sa.text("SELECT id, prompt_id, room_id, status, qr_hash FROM generation_jobs ORDER BY id")
        ).all()
        model_settings = connection.execute(
            sa.text("SELECT id, model_name FROM model_settings ORDER BY id")
        ).all()

    assert rooms == [
        (1, "ph000000", "Main", "openai/gpt-5-image", 1),
        (2, "room0002", "Second", "google/gemini-2.5-flash-image", 0),
    ]
    assert prompts == [(10, 1, "Prompt One")]
    assert jobs == [(20, 10, 1, "completed", "qr123")]
    assert model_settings == [(1, "openai/gpt-5-image")]


def test_check_postgres_ready_uses_simple_query(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'ready.db'}"

    assert check_postgres_ready(database_url=database_url) is True
