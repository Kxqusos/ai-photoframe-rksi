import importlib
from pathlib import Path


def test_default_sqlite_url_is_stable_across_working_directories(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)

    import app.db as db_module

    db_module = importlib.reload(db_module)

    expected_path = (Path(__file__).resolve().parents[1] / "photoframe.db").resolve()
    assert db_module.DATABASE_URL == f"sqlite:///{expected_path.as_posix()}"


def test_relative_sqlite_url_from_env_is_resolved_from_backend_directory(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./photoframe.db")
    monkeypatch.chdir(tmp_path)

    import app.db as db_module

    db_module = importlib.reload(db_module)

    expected_path = (Path(__file__).resolve().parents[1] / "photoframe.db").resolve()
    assert db_module.DATABASE_URL == f"sqlite:///{expected_path.as_posix()}"
