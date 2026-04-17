import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from photoframe_backend.shared.logging import configure_logging


def _find_file_handlers_for_path(path: Path) -> list[RotatingFileHandler]:
    root_logger = logging.getLogger()
    resolved = path.resolve()
    handlers: list[RotatingFileHandler] = []
    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename).resolve() == resolved:
            handlers.append(handler)
    return handlers


def test_configure_logging_writes_logs_to_file(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "backend.log"
    monkeypatch.setenv("LOG__FILE_PATH", str(log_path))
    monkeypatch.setenv("LOG__LEVEL", "INFO")

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level

    try:
        configure_logging()
        configure_logging()

        file_handlers = _find_file_handlers_for_path(log_path)
        assert len(file_handlers) == 1

        logger = logging.getLogger("app.test_logging")
        logger.info("file logging smoke test")

        for handler in file_handlers:
            handler.flush()

        content = log_path.read_text(encoding="utf-8")
        assert "file logging smoke test" in content
    finally:
        for handler in list(root_logger.handlers):
            if handler in original_handlers:
                continue
            root_logger.removeHandler(handler)
            handler.close()
        root_logger.setLevel(original_level)


def test_configure_logging_enables_verbose_dev_loggers(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "backend.log"
    monkeypatch.setenv("LOG__FILE_PATH", str(log_path))
    monkeypatch.setenv("LOG__LEVEL", "DEBUG")
    monkeypatch.setenv("LOG__DEV_VERBOSE", "true")

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    tracked_loggers = {
        name: logging.getLogger(name).level
        for name in ["sqlalchemy.engine", "sqlalchemy.pool", "uvicorn.error", "uvicorn.access"]
    }

    try:
        configure_logging()

        assert logging.getLogger("sqlalchemy.engine").level == logging.INFO
        assert logging.getLogger("sqlalchemy.pool").level == logging.DEBUG
        assert logging.getLogger("uvicorn.error").level == logging.DEBUG
        assert logging.getLogger("uvicorn.access").level == logging.DEBUG
    finally:
        for handler in list(root_logger.handlers):
            if handler in original_handlers:
                continue
            root_logger.removeHandler(handler)
            handler.close()
        root_logger.setLevel(original_level)
        for name, level in tracked_loggers.items():
            logging.getLogger(name).setLevel(level)
