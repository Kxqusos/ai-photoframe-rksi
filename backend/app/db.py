import os
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./photoframe.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_generation_jobs_qr_hash()


def _migrate_generation_jobs_qr_hash() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        table_exists = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='generation_jobs'")
        ).fetchone()
        if not table_exists:
            return

        columns = connection.execute(text("PRAGMA table_info(generation_jobs)")).fetchall()
        column_names = {str(row[1]) for row in columns}
        if "qr_hash" not in column_names:
            connection.execute(text("ALTER TABLE generation_jobs ADD COLUMN qr_hash VARCHAR(64)"))

        connection.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_generation_jobs_qr_hash ON generation_jobs (qr_hash)")
        )
