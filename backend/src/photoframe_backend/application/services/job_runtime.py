import mimetypes
import os
import shutil
import time
from urllib.parse import quote

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from photoframe_backend.infrastructure.clients import openrouter_client
from photoframe_backend.infrastructure.db.models import GenerationJob, ModelSetting, Prompt, Room
from photoframe_backend.application.services.job_service import JobService
from photoframe_backend.application.services.prompt_service import PromptService
from photoframe_backend.application.services.room_service import RoomService
from photoframe_backend.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from photoframe_backend.infrastructure.db.repositories.prompts import SqlAlchemyPromptRepository
from photoframe_backend.infrastructure.db.repositories.rooms import SqlAlchemyRoomRepository
from photoframe_backend.shared.constants import BACKEND_DIR
from photoframe_backend.shared.public_ids import DEFAULT_PUBLIC_ID, generate_public_id, is_public_id, normalize_public_id

BACKEND_ROOT = BACKEND_DIR
STORAGE_ROOT = BACKEND_ROOT / "storage"
LEGACY_STORAGE_ROOT = BACKEND_ROOT / "src" / "photoframe_backend" / "application" / "storage"
SOURCE_DIR = STORAGE_ROOT / "source"
RESULT_DIR = STORAGE_ROOT / "results"
DEFAULT_RESULT_RETENTION_DAYS = 7
_SECONDS_PER_DAY = 24 * 60 * 60

SOURCE_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL_NAME = "openai/gpt-5-image"
DEFAULT_PUBLIC_ROOM_SLUG = DEFAULT_PUBLIC_ID
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


def sync_legacy_storage() -> None:
    if not LEGACY_STORAGE_ROOT.exists():
        return

    for legacy_path in LEGACY_STORAGE_ROOT.rglob("*"):
        if not legacy_path.is_file():
            continue
        relative = legacy_path.relative_to(LEGACY_STORAGE_ROOT)
        target = STORAGE_ROOT / relative
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy_path, target)


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
    return generate_public_id()


def _generate_unique_qr_hash(db: Session) -> str:
    while True:
        candidate = _generate_qr_hash()
        exists = db.query(GenerationJob.id).filter(GenerationJob.qr_hash == candidate).first()
        if exists is None:
            return candidate


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
    service = JobService(
        room_service=RoomService(
            SqlAlchemyRoomRepository(db),
            default_room_slug=resolve_default_room_slug(),
            default_model_name=DEFAULT_MODEL_NAME,
        ),
        prompt_service=PromptService(SqlAlchemyPromptRepository(db)),
        job_repository=SqlAlchemyJobRepository(db, source_dir=SOURCE_DIR),
        generate_qr_hash=lambda: _generate_unique_qr_hash(db),
        generate_image=openrouter_client.generate_image,
        build_room_result_dir=_build_room_result_dir,
        build_filename=_build_filename,
        resolve_result_suffix=_resolve_result_suffix,
        prune_result_files=_prune_result_files,
        cleanup_source_file=_cleanup_source_file,
        default_model_name=DEFAULT_MODEL_NAME,
    )
    return service.create_processing_job_for_room_id(prompt_id=prompt_id, room_id=room_id, source_bytes=source_bytes)


def _normalize_model_name(raw_model_name: str | None) -> str:
    model_name = (raw_model_name or "").strip()
    if not model_name or model_name in {LEGACY_MODEL_NAME, LEGACY_OPENAI_MODEL_NAME, LEGACY_MINI_MODEL_NAME}:
        return DEFAULT_MODEL_NAME
    return model_name


def _resolve_model_name(db: Session) -> str:
    setting = db.get(ModelSetting, 1)
    if setting is None:
        return DEFAULT_MODEL_NAME
    return _normalize_model_name(setting.model_name)


def _resolve_model_name_for_room(room: Room) -> str:
    return _normalize_model_name(room.model_name)


def run_generation_sync(db: Session, job_id: int) -> GenerationJob:
    service = JobService(
        room_service=RoomService(
            SqlAlchemyRoomRepository(db),
            default_room_slug=resolve_default_room_slug(),
            default_model_name=DEFAULT_MODEL_NAME,
        ),
        prompt_service=PromptService(SqlAlchemyPromptRepository(db)),
        job_repository=SqlAlchemyJobRepository(db, source_dir=SOURCE_DIR),
        generate_qr_hash=_generate_qr_hash,
        generate_image=lambda *, model, prompt, image_bytes: openrouter_client.generate_image(
            model=_normalize_model_name(model),
            prompt=prompt,
            image_bytes=image_bytes,
        ),
        build_room_result_dir=_build_room_result_dir,
        build_filename=_build_filename,
        resolve_result_suffix=_resolve_result_suffix,
        prune_result_files=_prune_result_files,
        cleanup_source_file=_cleanup_source_file,
        default_model_name=DEFAULT_MODEL_NAME,
    )
    return service.run_generation_sync(job_id)


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
    if not value:
        return DEFAULT_PUBLIC_ROOM_SLUG
    if is_public_id(value):
        return normalize_public_id(value)
    return DEFAULT_PUBLIC_ROOM_SLUG


def get_room_by_slug(db: Session, room_slug: str, *, active_only: bool) -> Room | None:
    service = RoomService(
        SqlAlchemyRoomRepository(db),
        default_room_slug=resolve_default_room_slug(),
        default_model_name=DEFAULT_MODEL_NAME,
    )
    return service.get_room_by_slug(room_slug, active_only=active_only)


def get_or_create_default_room(db: Session) -> Room:
    service = RoomService(
        SqlAlchemyRoomRepository(db),
        default_room_slug=resolve_default_room_slug(),
        default_model_name=DEFAULT_MODEL_NAME,
    )
    return service.get_or_create_default_room()
