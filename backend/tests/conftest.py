import os
import tempfile
from pathlib import Path


_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="ai-photoframe-pytest-"))
_TEST_DB_PATH = _TEST_DB_DIR / "photoframe-test.db"
_TEST_DATABASE_URL = f"sqlite:///{_TEST_DB_PATH}"


def _force_pytest_database_env(*, include_test_database_url: bool = False) -> None:
    os.environ["APP__ENV"] = "test"
    os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
    if include_test_database_url:
        os.environ["TEST_DATABASE_URL"] = _TEST_DATABASE_URL
    else:
        os.environ.pop("TEST_DATABASE_URL", None)


_force_pytest_database_env()
