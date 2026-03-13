from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from photoframe_backend.infrastructure.db.session import _resolve_database_url
from photoframe_backend.infrastructure.settings.runtime import load_settings


def _cli_database_url() -> str:
    if any(key.startswith("DB__") for key in os.environ):
        return load_settings(allow_test_defaults=True).database_url
    return _resolve_database_url(os.getenv("DATABASE_URL"))


def run_migrations(database_url: str, revision: str = "head") -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)

    previous_test_database_url = os.environ.get("TEST_DATABASE_URL")
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["TEST_DATABASE_URL"] = database_url
    try:
        command.upgrade(config, revision)
    finally:
        if previous_test_database_url is None:
            os.environ.pop("TEST_DATABASE_URL", None)
        else:
            os.environ["TEST_DATABASE_URL"] = previous_test_database_url

        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url


if __name__ == "__main__":
    run_migrations(_cli_database_url())
