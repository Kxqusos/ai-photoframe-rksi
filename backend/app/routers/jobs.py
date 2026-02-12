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
    get_job_or_404,
    run_generation_sync,
)
from app.qr_service import build_qr_png
from app.schemas import JobCreated, JobStatusOut

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
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


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobCreated)
async def create_job(
    background_tasks: BackgroundTasks,
    photo: UploadFile,
    prompt_id: int = Form(...),
    db: Session = Depends(get_db),
) -> JobCreated:
    payload = await photo.read()
    job = create_processing_job(db, prompt_id=prompt_id, source_bytes=payload)
    background_tasks.add_task(_run_generation_in_background, job.id)
    return JobCreated(id=job.id, status=job.status)


@router.get("/{job_id}", response_model=JobStatusOut)
def get_job_status(job_id: int, db: Session = Depends(get_db)) -> JobStatusOut:
    job = get_job_or_404(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")

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


@router.get("/{job_id}/qr")
def download_qr(job_id: int, request: Request, db: Session = Depends(get_db)) -> Response:
    job = get_completed_job_or_404(db, job_id)
    if job is None:
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
