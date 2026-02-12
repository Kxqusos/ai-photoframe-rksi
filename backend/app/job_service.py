import os
from uuid import uuid4

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app import openrouter_client
from app.models import GenerationJob, ModelSetting, Prompt

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STORAGE_ROOT = BACKEND_ROOT / "storage"
SOURCE_DIR = STORAGE_ROOT / "source"
RESULT_DIR = STORAGE_ROOT / "results"
MAX_RESULT_FILES = 10

SOURCE_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL_NAME = "openai/gpt-5-image"
LEGACY_MODEL_NAME = "google/gemini-2.5-flash-image-preview"
LEGACY_OPENAI_MODEL_NAME = "openai/gpt-image-1"
LEGACY_MINI_MODEL_NAME = "openai/gpt-5-image-mini"


def _resolve_result_suffix() -> str:
    output_format = os.getenv("OPENROUTER_RESULT_FORMAT", "jpeg").strip().lower()
    if output_format == "png":
        return ".png"
    return ".jpg"


def _save_bytes(directory: Path, content: bytes, suffix: str) -> Path:
    filename = f"{Path.cwd().name}-{len(content)}-{id(content)}{suffix}"
    path = directory / filename
    path.write_bytes(content)
    return path


def _build_filename(job_id: int, suffix: str) -> str:
    return f"job-{job_id}{suffix}"


def _generate_qr_hash() -> str:
    return uuid4().hex[:16]


def _cleanup_source_file(path: str | None) -> None:
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        # Cleanup failure should not break the job lifecycle.
        return


def _prune_result_files(*, max_files: int = MAX_RESULT_FILES) -> None:
    if max_files <= 0:
        return

    files = [path for path in RESULT_DIR.iterdir() if path.is_file()]
    if len(files) <= max_files:
        return

    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for stale in files[max_files:]:
        try:
            stale.unlink(missing_ok=True)
        except OSError:
            continue


def create_processing_job(db: Session, *, prompt_id: int, source_bytes: bytes) -> GenerationJob:
    job = GenerationJob(prompt_id=prompt_id, status="processing")
    db.add(job)
    db.commit()
    db.refresh(job)

    source_path = SOURCE_DIR / _build_filename(job.id, ".jpg")
    source_path.write_bytes(source_bytes)
    job.source_path = str(source_path)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _resolve_model_name(db: Session) -> str:
    setting = db.get(ModelSetting, 1)
    if setting is None:
        return DEFAULT_MODEL_NAME

    model_name = setting.model_name.strip()
    if not model_name or model_name in {LEGACY_MODEL_NAME, LEGACY_OPENAI_MODEL_NAME, LEGACY_MINI_MODEL_NAME}:
        return DEFAULT_MODEL_NAME

    return model_name


def run_generation_sync(db: Session, job_id: int) -> GenerationJob:
    job = db.get(GenerationJob, job_id)
    if job is None:
        raise ValueError(f"job {job_id} not found")

    prompt = db.get(Prompt, job.prompt_id)
    if prompt is None:
        job.status = "error"
        job.error_message = "prompt not found"
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    source_path = job.source_path
    try:
        source_bytes = Path(source_path).read_bytes() if source_path else b""
        model_name = _resolve_model_name(db)
        generated = openrouter_client.generate_image(
            model=model_name,
            prompt=prompt.prompt,
            image_bytes=source_bytes,
        )

        result_path = RESULT_DIR / _build_filename(job.id, _resolve_result_suffix())
        result_path.write_bytes(generated)
        _prune_result_files()

        job.result_path = str(result_path)
        if not job.qr_hash:
            job.qr_hash = _generate_qr_hash()
        job.status = "completed"
        job.error_message = None
    except Exception as exc:
        job.status = "error"
        job.error_message = str(exc)
    finally:
        _cleanup_source_file(source_path)
        job.source_path = None

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job_or_404(db: Session, job_id: int) -> GenerationJob | None:
    return db.get(GenerationJob, job_id)


def get_completed_job_or_404(db: Session, job_id: int) -> GenerationJob | None:
    job = db.get(GenerationJob, job_id)
    if job is None or job.status != "completed" or not job.result_path:
        return None
    return job


def get_completed_job_by_qr_hash(db: Session, qr_hash: str) -> GenerationJob | None:
    return (
        db.query(GenerationJob)
        .filter(GenerationJob.qr_hash == qr_hash, GenerationJob.status == "completed")
        .first()
    )
