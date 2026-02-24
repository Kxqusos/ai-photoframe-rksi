import importlib
import sys
from pathlib import Path

from sqlalchemy import inspect


def _load_fresh_backend_modules(monkeypatch, tmp_path: Path):
    db_file = tmp_path / "rooms-schema.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    import app.db as db_module

    db_module = importlib.reload(db_module)

    sys.modules.pop("app.models", None)
    import app.models as models_module
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
        default_room = db.query(models_module.Room).filter(models_module.Room.slug == "main").first()
        assert default_room is not None
        assert default_room.is_active is True
