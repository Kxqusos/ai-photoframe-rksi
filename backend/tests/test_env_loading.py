from pathlib import Path
import os

from app.config import load_local_env


def test_load_local_env_sets_missing_variable(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OPENROUTER_API_KEY=from-file\n", encoding="utf-8")

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    load_local_env(env_path)

    assert os.getenv("OPENROUTER_API_KEY") == "from-file"


def test_load_local_env_does_not_override_existing_variable(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OPENROUTER_API_KEY=from-file\n", encoding="utf-8")

    monkeypatch.setenv("OPENROUTER_API_KEY", "from-env")
    load_local_env(env_path)

    assert os.getenv("OPENROUTER_API_KEY") == "from-env"
