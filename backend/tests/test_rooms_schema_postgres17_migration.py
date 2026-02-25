import os
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is not set; skipping PostgreSQL 17 Alembic migration integration test",
)


def _build_alembic_config() -> Config:
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    return config


def test_rooms_schema_postgres17_migration() -> None:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set")

    config = _build_alembic_config()
    os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL

    command.upgrade(config, "head")

    engine = sa.create_engine(TEST_DATABASE_URL)
    try:
        with engine.begin() as connection:
            inspector = sa.inspect(connection)

            assert "rooms" in inspector.get_table_names()

            room_indexes = {index["name"] for index in inspector.get_indexes("rooms")}
            assert "ix_rooms_slug" in room_indexes

            prompt_columns = {column["name"] for column in inspector.get_columns("prompts")}
            assert "room_id" in prompt_columns
            prompt_foreign_keys = inspector.get_foreign_keys("prompts")
            assert any(
                foreign_key.get("referred_table") == "rooms"
                and foreign_key.get("constrained_columns") == ["room_id"]
                for foreign_key in prompt_foreign_keys
            )

            job_columns = {column["name"] for column in inspector.get_columns("generation_jobs")}
            assert "room_id" in job_columns
            job_foreign_keys = inspector.get_foreign_keys("generation_jobs")
            assert any(
                foreign_key.get("referred_table") == "rooms"
                and foreign_key.get("constrained_columns") == ["room_id"]
                for foreign_key in job_foreign_keys
            )

            prompt_indexes = {index["name"] for index in inspector.get_indexes("prompts")}
            job_indexes = {index["name"] for index in inspector.get_indexes("generation_jobs")}
            assert "ix_prompts_room_id" in prompt_indexes
            assert "ix_generation_jobs_room_id" in job_indexes

            default_room_slug = connection.execute(
                sa.text("SELECT slug FROM rooms WHERE slug = :slug LIMIT 1"),
                {"slug": "main"},
            ).scalar_one_or_none()
            assert default_room_slug == "main"
    finally:
        engine.dispose()
