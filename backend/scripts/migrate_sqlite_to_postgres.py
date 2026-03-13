from __future__ import annotations

import argparse
import os
from pathlib import Path

import sqlalchemy as sa

from photoframe_backend.infrastructure.db.session import _resolve_database_url
from photoframe_backend.infrastructure.settings.runtime import load_settings

TABLE_COPY_ORDER = ("rooms", "model_settings", "prompts", "generation_jobs")
TABLE_COLUMNS = {
    "rooms": ("id", "slug", "name", "model_name", "is_active"),
    "model_settings": ("id", "model_name"),
    "prompts": ("id", "name", "description", "prompt", "preview_image_url", "icon_image_url", "room_id"),
    "generation_jobs": ("id", "prompt_id", "room_id", "status", "qr_hash", "source_path", "result_path", "error_message"),
}


def _cli_target_database_url() -> str:
    if any(key.startswith("DB__") for key in os.environ):
        return load_settings(allow_test_defaults=True).database_url
    return _resolve_database_url(os.getenv("DATABASE_URL"))


def _read_source_rows(connection: sa.Connection, table_name: str) -> list[dict[str, object]]:
    columns = TABLE_COLUMNS[table_name]
    result = connection.execute(sa.text(f"SELECT {', '.join(columns)} FROM {table_name} ORDER BY id"))
    return [dict(row._mapping) for row in result]


def _build_target_engine(target_database_url: str) -> sa.Engine:
    if not target_database_url.startswith("sqlite"):
        return sa.create_engine(target_database_url)

    engine = sa.create_engine(target_database_url, connect_args={"check_same_thread": False})

    @sa.event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _upsert_target_rows(connection: sa.Connection, table_name: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        return

    columns = TABLE_COLUMNS[table_name]
    mutable_columns = tuple(column for column in columns if column != "id")
    assignments = ", ".join(f"{column} = :{column}" for column in mutable_columns)
    placeholders = ", ".join(f":{column}" for column in columns)
    update_stmt = sa.text(f"UPDATE {table_name} SET {assignments} WHERE id = :id")
    insert_stmt = sa.text(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})")

    for row in rows:
        updated = connection.execute(update_stmt, row)
        if updated.rowcount == 0:
            connection.execute(insert_stmt, row)


def migrate_sqlite_to_postgres(source_sqlite_path: Path, target_database_url: str) -> None:
    source_engine = sa.create_engine(f"sqlite:///{Path(source_sqlite_path).resolve()}", connect_args={"check_same_thread": False})
    target_engine = _build_target_engine(target_database_url)

    try:
        with source_engine.connect() as source_connection, target_engine.begin() as target_connection:
            for table_name in TABLE_COPY_ORDER:
                _upsert_target_rows(target_connection, table_name, _read_source_rows(source_connection, table_name))
    finally:
        source_engine.dispose()
        target_engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy data from a legacy SQLite database into the configured target DB.")
    parser.add_argument("--source", default=None, help="Path to the legacy SQLite database file")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Target database URL. Defaults to grouped DB__* settings or DATABASE_URL.",
    )
    args = parser.parse_args()

    source_path = args.source or os.environ.get("SOURCE_SQLITE_PATH")
    if not source_path:
        raise SystemExit("Provide --source or SOURCE_SQLITE_PATH")

    migrate_sqlite_to_postgres(Path(source_path), args.database_url or _cli_target_database_url())


if __name__ == "__main__":
    main()
