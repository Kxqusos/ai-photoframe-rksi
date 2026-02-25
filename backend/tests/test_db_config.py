from pathlib import Path

import app.db as db_module


def test_default_sqlite_url_is_stable_across_working_directories(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    expected_path = (Path(__file__).resolve().parents[1] / "photoframe.db").resolve()
    assert db_module._resolve_database_url(None) == f"sqlite:///{expected_path.as_posix()}"


def test_relative_sqlite_url_from_env_is_resolved_from_backend_directory(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    expected_path = (Path(__file__).resolve().parents[1] / "photoframe.db").resolve()
    assert db_module._resolve_database_url("sqlite:///./photoframe.db") == f"sqlite:///{expected_path.as_posix()}"
