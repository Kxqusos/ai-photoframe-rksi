import mimetypes
import os
import time
from uuid import uuid4
from urllib.parse import quote

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app import openrouter_client
from app.models import GenerationJob, ModelSetting, Prompt, Room

BACKEND_ROOT = Path(__file__).resolve().parents[1]
STORAGE_ROOT = BACKEND_ROOT / "storage"
SOURCE_DIR = STORAGE_ROOT / "source"
RESULT_DIR = STORAGE_ROOT / "results"
DEFAULT_RESULT_RETENTION_DAYS = 7
_SECONDS_PER_DAY = 24 * 60 * 60

SOURCE_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL_NAME = "openai/gpt-5-image"
DEFAULT_PUBLIC_ROOM_SLUG = "main"
LEGACY_MODEL_NAME = "google/gemini-2.5-flash-image-preview"
LEGACY_OPENAI_MODEL_NAME = "openai/gpt-image-1"
LEGACY_MINI_MODEL_NAME = "openai/gpt-5-image-mini"
_GALLERY_IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".avif",
    ".heic",
    ".heif",
    ".jfif",
}


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


def _build_room_result_dir(room_slug: str) -> Path:
    path = RESULT_DIR / f"room-{room_slug}"
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def _resolve_result_retention_days() -> int:
    raw_days = os.getenv("RESULT_RETENTION_DAYS", str(DEFAULT_RESULT_RETENTION_DAYS)).strip()
    try:
        days = int(raw_days)
    except ValueError:
        return DEFAULT_RESULT_RETENTION_DAYS
    if days <= 0:
        return DEFAULT_RESULT_RETENTION_DAYS
    return days


def _prune_result_files() -> None:
    retention_days = _resolve_result_retention_days()
    cutoff_timestamp = time.time() - (retention_days * _SECONDS_PER_DAY)

    files = [path for path in RESULT_DIR.rglob("*") if path.is_file()]
    for stale in files:
        try:
            if stale.stat().st_mtime < cutoff_timestamp:
                stale.unlink(missing_ok=True)
        except OSError:
            continue


def _is_gallery_image_file(path: Path) -> bool:
    media_type, _ = mimetypes.guess_type(path.name)
    if media_type and media_type.startswith("image/"):
        return True
    return path.suffix.lower() in _GALLERY_IMAGE_SUFFIXES


def list_gallery_results(room_slug: str) -> list[dict[str, Any]]:
    room_dir = RESULT_DIR / f"room-{room_slug}"
    if not room_dir.exists():
        return []

    items: list[tuple[float, str]] = []
    for path in room_dir.iterdir():
        if not path.is_file() or not _is_gallery_image_file(path):
            continue
        try:
            modified_at = path.stat().st_mtime
        except OSError:
            continue
        items.append((modified_at, path.name))

    items.sort(key=lambda item: item[0], reverse=True)
    return [
        {"name": name, "url": f"/media/results/room-{room_slug}/{quote(name)}", "modified_at": modified_at}
        for modified_at, name in items
    ]


def create_processing_job(db: Session, *, prompt_id: int, room_id: int, source_bytes: bytes) -> GenerationJob:
    job = GenerationJob(prompt_id=prompt_id, room_id=room_id, status="processing")
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

        room = db.get(Room, job.room_id)
        if room is None:
            raise ValueError("room not found")

        result_dir = _build_room_result_dir(room.slug)
        result_path = result_dir / _build_filename(job.id, _resolve_result_suffix())
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
    return db.query(GenerationJob).filter(GenerationJob.qr_hash == qr_hash, GenerationJob.status == "completed").first()


def get_job_by_qr_hash(db: Session, qr_hash: str) -> GenerationJob | None:
    return db.query(GenerationJob).filter(GenerationJob.qr_hash == qr_hash).first()


def resolve_default_room_slug() -> str:
    value = os.getenv("DEFAULT_PUBLIC_ROOM_SLUG", DEFAULT_PUBLIC_ROOM_SLUG).strip()
    return value or DEFAULT_PUBLIC_ROOM_SLUG


def get_room_by_slug(db: Session, room_slug: str, *, active_only: bool) -> Room | None:
    query = db.query(Room).filter(Room.slug == room_slug)
    if active_only:
        query = query.filter(Room.is_active.is_(True))
    return query.first()


def get_or_create_default_room(db: Session) -> Room:
    default_slug = resolve_default_room_slug()
    room = db.query(Room).filter(Room.slug == default_slug).first()
    if room is not None:
        return room

    room = Room(slug=default_slug, name="Main", model_name=DEFAULT_MODEL_NAME, is_active=True)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room
