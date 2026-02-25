import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.job_service import (
    create_processing_job,
    get_completed_job_by_qr_hash,
    get_completed_job_or_404,
    get_job_by_qr_hash,
    get_job_or_404,
    get_or_create_default_room,
    get_room_by_slug,
    list_gallery_results,
    run_generation_sync,
)
from app.models import Prompt
from app.qr_service import build_qr_png
from app.schemas import GalleryImageOut, JobCreated, JobStatusOut

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
room_router = APIRouter(prefix="/api/rooms/{room_slug}/jobs", tags=["jobs"])
public_router = APIRouter(prefix="/qr", tags=["qr"])
logger = logging.getLogger(__name__)


def _build_qr_target_url(request: Request, qr_hash: str) -> str:
    return str(request.base_url).rstrip("/") + f"/qr/{qr_hash}"


def _run_generation_in_background(job_id: int) -> None:
    try:
        with SessionLocal() as db:
            run_generation_sync(db, job_id)
    except Exception:
        logger.exception("Background generation crashed for job %s", job_id)


def _to_job_status(job: object) -> JobStatusOut:
    if job.status == "completed":
        if not job.qr_hash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="job qr hash is not ready")
        download_url = f"/qr/{job.qr_hash}"
        return JobStatusOut(
            id=job.id,
            status=job.status,
            result_url=download_url,
            download_url=download_url,
            qr_url=f"/api/jobs/{job.id}/qr",
            error_message=job.error_message,
        )
    return JobStatusOut(id=job.id, status=job.status, error_message=job.error_message)


def _resolve_room_or_404(db: Session, room_slug: str):
    room = get_room_by_slug(db, room_slug, active_only=True)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="room not found")
    return room


async def _create_job_for_room(
    *,
    db: Session,
    room_slug: str,
    prompt_id: int,
    photo: UploadFile,
    background_tasks: BackgroundTasks,
) -> JobCreated:
    room = _resolve_room_or_404(db, room_slug)
    prompt = db.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="prompt not found")
    if prompt.room_id != room.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="prompt does not belong to room")

    payload = await photo.read()
    job = create_processing_job(db, prompt_id=prompt_id, room_id=room.id, source_bytes=payload)
    background_tasks.add_task(_run_generation_in_background, job.id)
    return JobCreated(id=job.id, status=job.status)


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobCreated)
async def create_job(
    background_tasks: BackgroundTasks,
    photo: UploadFile,
    prompt_id: int = Form(...),
    db: Session = Depends(get_db),
) -> JobCreated:
    default_room = get_or_create_default_room(db)
    return await _create_job_for_room(
        db=db,
        room_slug=default_room.slug,
        prompt_id=prompt_id,
        photo=photo,
        background_tasks=background_tasks,
    )


@room_router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobCreated)
async def create_job_for_room(
    room_slug: str,
    background_tasks: BackgroundTasks,
    photo: UploadFile,
    prompt_id: int = Form(...),
    db: Session = Depends(get_db),
) -> JobCreated:
    return await _create_job_for_room(
        db=db,
        room_slug=room_slug,
        prompt_id=prompt_id,
        photo=photo,
        background_tasks=background_tasks,
    )


@router.get("/gallery", response_model=list[GalleryImageOut])
def get_gallery_images(db: Session = Depends(get_db)) -> list[GalleryImageOut]:
    default_room = get_or_create_default_room(db)
    rows = list_gallery_results(default_room.slug)
    return [GalleryImageOut(**row) for row in rows]


@room_router.get("/gallery", response_model=list[GalleryImageOut])
def get_gallery_images_for_room(room_slug: str, db: Session = Depends(get_db)) -> list[GalleryImageOut]:
    room = _resolve_room_or_404(db, room_slug)
    rows = list_gallery_results(room.slug)
    return [GalleryImageOut(**row) for row in rows]


@router.get("/hash/{jpg_hash}", response_model=JobStatusOut)
def get_job_status_by_hash(jpg_hash: str, db: Session = Depends(get_db)) -> JobStatusOut:
    default_room = get_or_create_default_room(db)
    job = get_job_by_qr_hash(db, jpg_hash)
    if job is None or job.room_id != default_room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return _to_job_status(job)


@room_router.get("/hash/{jpg_hash}", response_model=JobStatusOut)
def get_job_status_by_hash_for_room(room_slug: str, jpg_hash: str, db: Session = Depends(get_db)) -> JobStatusOut:
    room = _resolve_room_or_404(db, room_slug)
    job = get_job_by_qr_hash(db, jpg_hash)
    if job is None or job.room_id != room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return _to_job_status(job)


@router.get("/{job_id}", response_model=JobStatusOut)
def get_job_status(job_id: int, db: Session = Depends(get_db)) -> JobStatusOut:
    default_room = get_or_create_default_room(db)
    job = get_job_or_404(db, job_id)
    if job is None or job.room_id != default_room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return _to_job_status(job)


@router.get("/{job_id}/qr")
def download_qr(job_id: int, request: Request, db: Session = Depends(get_db)) -> Response:
    default_room = get_or_create_default_room(db)
    job = get_completed_job_or_404(db, job_id)
    if job is None or job.room_id != default_room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not completed")
    if not job.qr_hash:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="job qr hash is not ready")

    target_url = _build_qr_target_url(request, job.qr_hash)
    png_bytes = build_qr_png(target_url)
    return Response(content=png_bytes, media_type="image/png")


@public_router.get("/{qr_hash}")
def download_result_by_qr_hash(qr_hash: str, db: Session = Depends(get_db)) -> FileResponse:
    job = get_completed_job_by_qr_hash(db, qr_hash)
    if job is None or not job.result_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="qr hash not found")
    result_path = Path(job.result_path)
    if not result_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="result not found")
    suffix = result_path.suffix or ".jpg"
    return FileResponse(result_path, filename=f"photoframe-{job.id}{suffix}")
