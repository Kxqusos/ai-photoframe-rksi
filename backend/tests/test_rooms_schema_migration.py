from pathlib import Path
import re

from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker


def _load_fresh_backend_modules(monkeypatch, tmp_path: Path):
    import app.db as db_module
    import app.models as models_module

    db_file = tmp_path / "rooms-schema.db"
    database_url = f"sqlite:///{db_file}"
    test_engine = db_module.create_engine(database_url, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(db_module, "DATABASE_URL", database_url)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", test_session_local)

    db_module.init_db()
    return db_module, models_module


def test_rooms_table_exists_with_unique_slug(monkeypatch, tmp_path: Path) -> None:
    db_module, _ = _load_fresh_backend_modules(monkeypatch, tmp_path)
    inspector = inspect(db_module.engine)

    assert "rooms" in inspector.get_table_names()
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
    import app.db as db_module

    db_file = tmp_path / "rooms-schema-legacy.db"
    database_url = f"sqlite:///{db_file}"
    test_engine = db_module.create_engine(database_url, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(db_module, "DATABASE_URL", database_url)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(db_module, "generate_public_id", lambda: "zzzzzzzz")

    db_module.Base.metadata.create_all(bind=test_engine)
    with test_engine.begin() as connection:
        connection.execute(
            db_module.text(
                """
                INSERT INTO rooms (slug, name, model_name, is_active)
                VALUES ('main', 'Main', 'openai/gpt-5-image', 1),
                       ('8march', 'Room Legacy', 'openai/gpt-5-image', 1)
                """
            )
        )

    db_module.init_db()

    with db_module.SessionLocal() as db:
        slugs = [row[0] for row in db.execute(db_module.text("SELECT slug FROM rooms ORDER BY id ASC")).all()]
    assert "main" not in slugs
    assert "8march" not in slugs
    assert "ph000000" in slugs
    assert all(re.fullmatch(r"[a-z0-9]{8}", slug) for slug in slugs)


def test_default_room_insert_tolerates_existing_primary_key_on_postgres_path(monkeypatch, tmp_path: Path) -> None:
    import app.db as db_module

    db_file = tmp_path / "rooms-schema-postgres-conflict.db"
    database_url = f"sqlite:///{db_file}"
    test_engine = db_module.create_engine(database_url, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(db_module, "DATABASE_URL", "postgresql://example/test")
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", test_session_local)

    db_module.Base.metadata.create_all(bind=test_engine)
    with test_engine.begin() as connection:
        connection.execute(
            db_module.text(
                """
                INSERT INTO rooms (id, slug, name, model_name, is_active)
                VALUES (1, 'aaaaaaaa', 'Legacy Primary', 'openai/gpt-5-image', 1)
                """
            )
        )

    with test_engine.begin() as connection:
        db_module._ensure_default_room_exists(connection)
        rows = connection.execute(
            db_module.text("SELECT id, slug FROM rooms ORDER BY id ASC")
        ).fetchall()

    assert any(row[1] == "ph000000" for row in rows)


def test_init_db_skips_runtime_schema_bootstrap_for_postgres(monkeypatch) -> None:
    import app.db as db_module

    monkeypatch.setattr(db_module, "DATABASE_URL", "postgresql://example/test")

    calls: list[str] = []

    monkeypatch.setattr(db_module.Base.metadata, "create_all", lambda bind: calls.append("create_all"))
    monkeypatch.setattr(db_module, "_migrate_rooms_schema", lambda: calls.append("migrate_rooms"))
    monkeypatch.setattr(db_module, "_migrate_generation_jobs_qr_hash", lambda: calls.append("migrate_qr"))

    db_module.init_db()

    assert calls == []
