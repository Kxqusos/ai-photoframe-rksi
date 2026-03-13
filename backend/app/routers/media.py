from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MEDIA_ROOT = BACKEND_ROOT / "storage"
PREVIEW_DIR = MEDIA_ROOT / "previews"
ICON_DIR = MEDIA_ROOT / "icons"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
ICON_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/media", tags=["media"])


async def read_validated_image_upload(file: UploadFile, *, max_bytes: int | None = None) -> bytes:
    size_limit = MAX_UPLOAD_BYTES if max_bytes is None else max_bytes
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file must be an image")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file is empty")
    if len(payload) > size_limit:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="file is too large")

    try:
        with Image.open(BytesIO(payload)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file must be a valid image") from exc

    return payload


def _save_upload(payload: bytes, directory: Path, extension: str) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    path = directory / filename
    path.write_bytes(payload)
    return filename


def _room_media_subdir(base_dir: Path, room_id: int) -> Path:
    return base_dir / f"room-{room_id}"


async def save_prompt_preview(file: UploadFile, room_id: int | None = None) -> str:
    payload = await read_validated_image_upload(file)
    if room_id is None:
        filename = _save_upload(payload, PREVIEW_DIR, ".jpg")
        return f"/media/previews/{filename}"

    target_dir = _room_media_subdir(PREVIEW_DIR, room_id)
    filename = _save_upload(payload, target_dir, ".jpg")
    return f"/media/previews/room-{room_id}/{filename}"


async def save_prompt_icon(file: UploadFile, room_id: int | None = None) -> str:
    payload = await read_validated_image_upload(file)
    if room_id is None:
        filename = _save_upload(payload, ICON_DIR, ".png")
        return f"/media/icons/{filename}"

    target_dir = _room_media_subdir(ICON_DIR, room_id)
    filename = _save_upload(payload, target_dir, ".png")
    return f"/media/icons/room-{room_id}/{filename}"


@router.post("/prompt-preview", status_code=status.HTTP_201_CREATED)
async def upload_prompt_preview(file: UploadFile) -> dict[str, str]:
    return {"url": await save_prompt_preview(file)}


@router.post("/prompt-icon", status_code=status.HTTP_201_CREATED)
async def upload_prompt_icon(file: UploadFile) -> dict[str, str]:
    return {"url": await save_prompt_icon(file)}
