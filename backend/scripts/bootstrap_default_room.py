from __future__ import annotations

import os

from photoframe_backend.infrastructure.db.bootstrap import bootstrap_default_room as bootstrap_default_room_impl
from photoframe_backend.infrastructure.db.session import _resolve_database_url, build_engine
from photoframe_backend.infrastructure.settings.runtime import load_settings


def _cli_database_url() -> str:
    if any(key.startswith("DB__") for key in os.environ):
        return load_settings(allow_test_defaults=True).database_url
    return _resolve_database_url(os.getenv("DATABASE_URL"))


def bootstrap_default_room(
    engine=None,
    database_url: str | None = None,
    default_room_slug: str = "ph000000",
    fallback_room_password: str = "",
) -> None:
    resolved_database_url = database_url or os.environ["DATABASE_URL"]
    resolved_engine = engine or build_engine(resolved_database_url)
    bootstrap_default_room_impl(
        engine=resolved_engine,
        database_url=resolved_database_url,
        default_room_slug=default_room_slug,
        fallback_room_password=fallback_room_password,
    )


if __name__ == "__main__":
    bootstrap_default_room(database_url=_cli_database_url())
