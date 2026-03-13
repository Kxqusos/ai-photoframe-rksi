import os
from pathlib import Path
import runpy

from alembic import command
from alembic.config import Config
import sqlalchemy as sa
from fastapi.testclient import TestClient

import photoframe_backend.infrastructure.db.runtime as db_module
import photoframe_backend.main as main_module
from scripts.bootstrap_default_room import bootstrap_default_room
from scripts.run_migrations import run_migrations


def _build_alembic_config(database_url: str) -> Config:
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_app_startup_does_not_run_schema_mutation(monkeypatch, tmp_path: Path) -> None:
    import photoframe_backend.infrastructure.db.bootstrap as bootstrap_module

    database_url = f"sqlite:///{tmp_path / 'startup.db'}"
    test_engine = db_module.create_engine(database_url, connect_args={"check_same_thread": False})

    def fail(*args, **kwargs):
        raise AssertionError("runtime schema mutation was called on startup")

    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "DATABASE_URL", database_url)
    monkeypatch.setattr(main_module, "configure_logging", lambda: Path(tmp_path / "backend.log"))
    monkeypatch.setattr(db_module.Base.metadata, "create_all", fail)
    monkeypatch.setattr(bootstrap_module, "_migrate_rooms_schema", fail)
    monkeypatch.setattr(bootstrap_module, "_migrate_generation_jobs_qr_hash", fail)

    with TestClient(main_module.app):
        pass


def test_default_room_bootstrap_is_idempotent_after_migrations(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bootstrap.db'}"
    engine = sa.create_engine(database_url, connect_args={"check_same_thread": False})

    run_migrations(database_url)
    with engine.begin() as connection:
        connection.execute(sa.text("DELETE FROM rooms"))

    bootstrap_default_room(engine=engine, database_url=database_url)
    bootstrap_default_room(engine=engine, database_url=database_url)

    with engine.begin() as connection:
        rows = connection.execute(sa.text("SELECT slug, name, model_name FROM rooms")).all()

    assert rows == [("ph000000", "Main", "openai/gpt-5-image")]


def test_cli_helpers_use_grouped_db_env_only(monkeypatch) -> None:
    captured: dict[str, str] = {}

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP__ENV", "test")
    monkeypatch.setenv("DB__HOST", "postgres.internal")
    monkeypatch.setenv("DB__PORT", "5433")
    monkeypatch.setenv("DB__NAME", "photoframe_cli")
    monkeypatch.setenv("DB__USER", "cli_user")
    monkeypatch.setenv("DB__PASSWORD", "cli_pass")

    def fake_upgrade(config: Config, revision: str) -> None:
        captured["migrations_url"] = config.get_main_option("sqlalchemy.url")
        captured["revision"] = revision

    def fake_bootstrap_default_room(*, engine, database_url: str, default_room_slug: str) -> None:
        captured["bootstrap_url"] = database_url
        captured["bootstrap_slug"] = default_room_slug

    monkeypatch.setattr("alembic.command.upgrade", fake_upgrade)
    monkeypatch.setattr(
        "photoframe_backend.infrastructure.db.bootstrap.bootstrap_default_room",
        fake_bootstrap_default_room,
    )

    runpy.run_path(Path(__file__).resolve().parents[1] / "scripts" / "run_migrations.py", run_name="__main__")
    runpy.run_path(Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_default_room.py", run_name="__main__")

    expected_database_url = "postgresql+psycopg://cli_user:cli_pass@postgres.internal:5433/photoframe_cli"
    assert captured["migrations_url"] == expected_database_url
    assert captured["revision"] == "head"
    assert captured["bootstrap_url"] == expected_database_url
    assert captured["bootstrap_slug"] == "ph000000"


def test_bootstrap_default_room_downgrade_keeps_default_room(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'downgrade.db'}"
    engine = sa.create_engine(database_url, connect_args={"check_same_thread": False})
    config = _build_alembic_config(database_url)

    run_migrations(database_url)
    previous_test_database_url = os.environ.get("TEST_DATABASE_URL")
    os.environ["TEST_DATABASE_URL"] = database_url
    try:
        command.downgrade(config, "20260224_01_rooms_pg17")
    finally:
        if previous_test_database_url is None:
            os.environ.pop("TEST_DATABASE_URL", None)
        else:
            os.environ["TEST_DATABASE_URL"] = previous_test_database_url

    with engine.begin() as connection:
        room_slug = connection.execute(
            sa.text("SELECT slug FROM rooms WHERE slug = :slug"),
            {"slug": "ph000000"},
        ).scalar_one_or_none()

    assert room_slug == "ph000000"
