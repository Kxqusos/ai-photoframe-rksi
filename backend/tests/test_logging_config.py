import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import configure_logging


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
    monkeypatch.setenv("LOG_FILE_PATH", str(log_path))
    monkeypatch.setenv("LOG_LEVEL", "INFO")

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
