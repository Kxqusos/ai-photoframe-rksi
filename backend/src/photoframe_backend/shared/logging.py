import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from photoframe_backend.infrastructure.settings.loader import load_env_file
from photoframe_backend.infrastructure.settings.runtime import load_settings
from photoframe_backend.shared.constants import DEFAULT_ENV_FILE, DEFAULT_LOG_BACKUP_COUNT, DEFAULT_LOG_FORMAT, DEFAULT_LOG_MAX_BYTES


def load_local_env(env_path: Path | None = None) -> None:
    load_env_file(env_path or DEFAULT_ENV_FILE)


def _current_settings():
    return load_settings(allow_test_defaults=True)


def _resolve_log_file_path() -> Path:
    return _current_settings().log_file_path


def _resolve_log_level() -> int:
    raw_level = _current_settings().log.level.strip().upper()
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
        maxBytes=DEFAULT_LOG_MAX_BYTES,
        backupCount=DEFAULT_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    root_logger.addHandler(file_handler)

    level = _resolve_log_level()
    if root_logger.level == logging.NOTSET or root_logger.level > level:
        root_logger.setLevel(level)

    return target


__all__ = ["configure_logging", "load_local_env"]
