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
    extension = _extension_from_filename(file.filename, fallback_ext)
    filename = f"{uuid4().hex}{extension}"
    path = directory / filename
    path.write_bytes(await file.read())
    return filename


@router.post("/prompt-preview", status_code=status.HTTP_201_CREATED)
async def upload_prompt_preview(file: UploadFile) -> dict[str, str]:
    filename = await _save_upload(file, PREVIEW_DIR, ".jpg")
    return {"url": f"/media/previews/{filename}"}


@router.post("/prompt-icon", status_code=status.HTTP_201_CREATED)
async def upload_prompt_icon(file: UploadFile) -> dict[str, str]:
    filename = await _save_upload(file, ICON_DIR, ".png")
    return {"url": f"/media/icons/{filename}"}
