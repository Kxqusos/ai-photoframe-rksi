from pathlib import Path
import re

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from photoframe_backend.infrastructure.db.base import Base as SrcBase
from scripts.bootstrap_default_room import bootstrap_default_room
from scripts.run_migrations import run_migrations


def _load_fresh_backend_modules(monkeypatch, tmp_path: Path):
    import photoframe_backend.infrastructure.db.runtime as db_module
    import photoframe_backend.infrastructure.db.models as models_module

    db_file = tmp_path / "rooms-schema.db"
    database_url = f"sqlite:///{db_file}"
    test_engine = db_module.create_engine(database_url, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(db_module, "DATABASE_URL", database_url)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", test_session_local)

    run_migrations(database_url)
    bootstrap_default_room(engine=test_engine, database_url=database_url, default_room_slug=db_module.DEFAULT_ROOM_SLUG)
    return db_module, models_module


def test_rooms_table_exists_with_unique_slug(monkeypatch, tmp_path: Path) -> None:
    db_module, _ = _load_fresh_backend_modules(monkeypatch, tmp_path)
    inspector = inspect(db_module.engine)

    assert "rooms" in inspector.get_table_names()
    assert db_module.Base is SrcBase
    unique_constraints = inspector.get_unique_constraints("rooms")
    unique_indexes = inspector.get_indexes("rooms")
    assert (
        any(constraint.get("column_names") == ["slug"] for constraint in unique_constraints)
        or any(index.get("column_names") == ["slug"] and index.get("unique") for index in unique_indexes)
    )


def test_prompts_has_room_id_foreign_key(monkeypatch, tmp_path: Path) -> None:
    db_module, _ = _load_fresh_backend_modules(monkeypatch, tmp_path)
    inspector = inspect(db_module.engine)

    prompt_columns = {column["name"] for column in inspector.get_columns("prompts")}
    assert "room_id" in prompt_columns

    prompt_foreign_keys = inspector.get_foreign_keys("prompts")
    assert any(
        foreign_key.get("constrained_columns") == ["room_id"] and foreign_key.get("referred_table") == "rooms"
        for foreign_key in prompt_foreign_keys
    )


def test_generation_jobs_has_room_id_foreign_key(monkeypatch, tmp_path: Path) -> None:
    db_module, _ = _load_fresh_backend_modules(monkeypatch, tmp_path)
    inspector = inspect(db_module.engine)

    job_columns = {column["name"] for column in inspector.get_columns("generation_jobs")}
    assert "room_id" in job_columns

    job_foreign_keys = inspector.get_foreign_keys("generation_jobs")
    assert any(
        foreign_key.get("constrained_columns") == ["room_id"] and foreign_key.get("referred_table") == "rooms"
        for foreign_key in job_foreign_keys
    )


def test_default_room_is_created_on_startup(monkeypatch, tmp_path: Path) -> None:
    db_module, models_module = _load_fresh_backend_modules(monkeypatch, tmp_path)

    with db_module.SessionLocal() as db:
        default_room = db.query(models_module.Room).filter(models_module.Room.slug == "ph000000").first()
        assert default_room is not None
        assert default_room.is_active is True


def test_legacy_room_slugs_are_migrated_to_public_id_format(monkeypatch, tmp_path: Path) -> None:
    import photoframe_backend.infrastructure.db.runtime as db_module

    db_file = tmp_path / "rooms-schema-legacy.db"
    database_url = f"sqlite:///{db_file}"
    test_engine = db_module.create_engine(database_url, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(db_module, "DATABASE_URL", database_url)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", test_session_local)

    with test_engine.begin() as connection:
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
                INSERT INTO rooms (slug, name, model_name, is_active)
                VALUES ('main', 'Main', 'openai/gpt-5-image', 1),
                       ('8march', 'Room Legacy', 'openai/gpt-5-image', 1)
                """
            )
        )

    run_migrations(database_url)
    bootstrap_default_room(engine=test_engine, database_url=database_url, default_room_slug=db_module.DEFAULT_ROOM_SLUG)

    with db_module.SessionLocal() as db:
        slugs = [row[0] for row in db.execute(db_module.text("SELECT slug FROM rooms ORDER BY id ASC")).all()]
    assert "main" not in slugs
    assert "8march" not in slugs
    assert "ph000000" in slugs
    assert all(re.fullmatch(r"[a-z0-9]{8}", slug) for slug in slugs)
