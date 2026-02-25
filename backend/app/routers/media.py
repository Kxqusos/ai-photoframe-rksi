from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, status

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MEDIA_ROOT = BACKEND_ROOT / "storage"
PREVIEW_DIR = MEDIA_ROOT / "previews"
ICON_DIR = MEDIA_ROOT / "icons"

PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
ICON_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/media", tags=["media"])


def _extension_from_filename(filename: str | None, fallback: str) -> str:
    if not filename or "." not in filename:
        return fallback
    return "." + filename.rsplit(".", 1)[-1].lower()


async def _save_upload(file: UploadFile, directory: Path, fallback_ext: str) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    extension = _extension_from_filename(file.filename, fallback_ext)
    filename = f"{uuid4().hex}{extension}"
    path = directory / filename
    path.write_bytes(await file.read())
    return filename


def _room_media_subdir(base_dir: Path, room_id: int) -> Path:
    return base_dir / f"room-{room_id}"


async def save_prompt_preview(file: UploadFile, room_id: int | None = None) -> str:
    if room_id is None:
        filename = await _save_upload(file, PREVIEW_DIR, ".jpg")
        return f"/media/previews/{filename}"

    target_dir = _room_media_subdir(PREVIEW_DIR, room_id)
    filename = await _save_upload(file, target_dir, ".jpg")
    return f"/media/previews/room-{room_id}/{filename}"


async def save_prompt_icon(file: UploadFile, room_id: int | None = None) -> str:
    if room_id is None:
        filename = await _save_upload(file, ICON_DIR, ".png")
        return f"/media/icons/{filename}"

    target_dir = _room_media_subdir(ICON_DIR, room_id)
    filename = await _save_upload(file, target_dir, ".png")
    return f"/media/icons/room-{room_id}/{filename}"


@router.post("/prompt-preview", status_code=status.HTTP_201_CREATED)
async def upload_prompt_preview(file: UploadFile) -> dict[str, str]:
    return {"url": await save_prompt_preview(file)}


@router.post("/prompt-icon", status_code=status.HTTP_201_CREATED)
async def upload_prompt_icon(file: UploadFile) -> dict[str, str]:
    return {"url": await save_prompt_icon(file)}
