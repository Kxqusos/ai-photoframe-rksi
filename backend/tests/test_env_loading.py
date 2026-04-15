from pathlib import Path
import os

from photoframe_backend.shared.logging import load_local_env


def test_load_local_env_sets_missing_variable(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("AUTH__JWT_SECRET=from-file\n", encoding="utf-8")

    monkeypatch.delenv("AUTH__JWT_SECRET", raising=False)
    load_local_env(env_path)

    assert os.getenv("AUTH__JWT_SECRET") == "from-file"


def test_load_local_env_does_not_override_existing_variable(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("AUTH__JWT_SECRET=from-file\n", encoding="utf-8")

    monkeypatch.setenv("AUTH__JWT_SECRET", "from-env")
    load_local_env(env_path)

    assert os.getenv("AUTH__JWT_SECRET") == "from-env"


def test_load_local_env_strips_wrapping_quotes(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text('APP__NAME="Quoted App"\n', encoding="utf-8")

    monkeypatch.delenv("APP__NAME", raising=False)
    load_local_env(env_path)

    assert os.getenv("APP__NAME") == "Quoted App"
