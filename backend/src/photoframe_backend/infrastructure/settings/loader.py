import os
from pathlib import Path

from photoframe_backend.shared.constants import DEFAULT_ENV_FILE


def load_env_file(env_path: Path | None = None) -> tuple[Path, set[str]]:
    path = env_path or DEFAULT_ENV_FILE
    if not path.exists():
        return path, set()

    inserted_keys: set[str] = set()

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        normalized = value.strip()
        if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"'", '"'}:
            normalized = normalized[1:-1]

        if key not in os.environ:
            os.environ[key] = normalized
            inserted_keys.add(key)

    return path, inserted_keys
