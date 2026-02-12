import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pydantic import BaseModel

_BASE_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_LOG_FILE_PATH = _BASE_DIR / "logs" / "backend.log"
_DEFAULT_LOG_LEVEL = "INFO"
_DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024
_DEFAULT_LOG_BACKUP_COUNT = 3
_DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def load_local_env(env_path: Path | None = None) -> None:
    path = env_path or (_BASE_DIR / ".env")
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


load_local_env()


def _resolve_log_file_path() -> Path:
    raw_path = os.getenv("LOG_FILE_PATH")
    if not raw_path:
        return _DEFAULT_LOG_FILE_PATH

    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (_BASE_DIR / candidate).resolve()


def _resolve_log_level() -> int:
    raw_level = os.getenv("LOG_LEVEL", _DEFAULT_LOG_LEVEL).strip().upper()
    parsed_level = getattr(logging, raw_level, None)
    return parsed_level if isinstance(parsed_level, int) else logging.INFO


def configure_logging() -> Path:
    log_file_path = _resolve_log_file_path()
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    target = log_file_path.resolve()

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename).resolve() == target:
            return target

    file_handler = RotatingFileHandler(
        target,
        maxBytes=_DEFAULT_LOG_MAX_BYTES,
        backupCount=_DEFAULT_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_DEFAULT_LOG_FORMAT))
    root_logger.addHandler(file_handler)

    level = _resolve_log_level()
    if root_logger.level == logging.NOTSET or root_logger.level > level:
        root_logger.setLevel(level)

    return target


class Settings(BaseModel):
    app_name: str = "AI Photoframe API"


settings = Settings()
