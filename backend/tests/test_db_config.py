import os
from pathlib import Path

import photoframe_backend.infrastructure.db.runtime as db_module
import conftest as test_conftest
from photoframe_backend.infrastructure.settings.runtime import load_settings


def test_default_runtime_database_url_uses_postgres_settings_defaults() -> None:
    settings = load_settings(allow_test_defaults=True)

    assert db_module._resolve_database_url(None) == settings.database_url
    assert db_module._resolve_database_url(None).startswith("postgresql+psycopg://")


def test_relative_sqlite_url_from_env_is_resolved_from_backend_directory(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    expected_path = (Path(__file__).resolve().parents[1] / "photoframe.db").resolve()
    assert db_module._resolve_database_url("sqlite:///./photoframe.db") == f"sqlite:///{expected_path.as_posix()}"


def test_alembic_env_imports_src_metadata_contract() -> None:
    text = (Path(__file__).resolve().parents[1] / "alembic" / "env.py").read_text(encoding="utf-8")

    assert "photoframe_backend.infrastructure.db" in text


def test_pytest_db_isolation_overrides_preexisting_runtime_database_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://prod:prod@db.example:5432/prod")
    monkeypatch.setenv("DB__HOST", "postgres.internal")
    monkeypatch.setenv("DB__PORT", "5433")
    monkeypatch.setenv("DB__NAME", "photoframe_test")
    monkeypatch.setenv("DB__USER", "pytest_user")
    monkeypatch.setenv("DB__PASSWORD", "pytest_pass")

    test_conftest._force_pytest_database_env(include_test_database_url=True)

    assert Path(test_conftest._TEST_DB_PATH).name == "photoframe-test.db"
    assert Path(test_conftest._TEST_DB_DIR).name.startswith("ai-photoframe-pytest-")
    assert Path(test_conftest._TEST_DB_PATH).is_absolute()
    assert os.environ["DATABASE_URL"] == test_conftest._TEST_DATABASE_URL
    assert os.environ["TEST_DATABASE_URL"] == test_conftest._TEST_DATABASE_URL
    assert load_settings(allow_test_defaults=True).database_url == (
        "postgresql+psycopg://pytest_user:pytest_pass@postgres.internal:5433/photoframe_test"
    )
