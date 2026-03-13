from __future__ import annotations

import argparse
import os

import sqlalchemy as sa

from photoframe_backend.infrastructure.db.session import _resolve_database_url
from photoframe_backend.infrastructure.settings.runtime import load_settings


def _cli_database_url() -> str:
    if any(key.startswith("DB__") for key in os.environ):
        return load_settings(allow_test_defaults=True).database_url
    return _resolve_database_url(os.getenv("DATABASE_URL"))


def check_postgres_ready(database_url: str) -> bool:
    engine = sa.create_engine(database_url)
    try:
        with engine.connect() as connection:
            return connection.execute(sa.text("SELECT 1")).scalar_one() == 1
    except sa.exc.SQLAlchemyError:
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check whether the configured PostgreSQL database is reachable.")
    parser.add_argument("--database-url", dest="database_url", default=None)
    args = parser.parse_args()
    raise SystemExit(0 if check_postgres_ready(args.database_url or _cli_database_url()) else 1)
