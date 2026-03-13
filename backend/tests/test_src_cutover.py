from pathlib import Path
import re


def test_src_entrypoint_imports_without_legacy_app_package() -> None:
    from photoframe_backend.main import app

    assert app.title


def test_backend_python_files_no_longer_import_legacy_app_package() -> None:
    project_root = Path(__file__).resolve().parents[1]
    roots = [project_root / "src", project_root / "tests"]
    forbidden_patterns = (
        re.compile(r"^\s*from app(?:\.|\s)", re.MULTILINE),
        re.compile(r"^\s*import app(?:\.|\s|$)", re.MULTILINE),
    )

    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if any(pattern.search(text) for pattern in forbidden_patterns):
                offenders.append(str(path.relative_to(project_root)))

    assert offenders == []
