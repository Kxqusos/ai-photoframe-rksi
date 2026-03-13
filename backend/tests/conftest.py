import os
import shutil
import tempfile
from pathlib import Path

_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="ai-photoframe-pytest-"))
_TEST_DB_PATH = _TEST_DB_DIR / "photoframe-test.db"

# Force pytest runs onto a disposable sqlite database so test helpers that
# recreate schema never touch the developer's working database file.
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH.as_posix()}"


def pytest_sessionfinish(session, exitstatus) -> None:  # type: ignore[no-untyped-def]
    shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)
