from pathlib import Path

from sqlalchemy.orm import Session

from photoframe_backend.infrastructure.db.models import GenerationJob


class SqlAlchemyJobRepository:
    def __init__(self, db: Session, *, source_dir: Path) -> None:
        self._db = db
        self._source_dir = source_dir

    def create_processing_job(self, *, prompt_id: int, room_id: int, source_bytes: bytes, qr_hash: str) -> GenerationJob:
        job = GenerationJob(prompt_id=prompt_id, room_id=room_id, status="processing", qr_hash=qr_hash)
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)

        source_path = self._source_dir / f"job-{job.id}.jpg"
        source_path.write_bytes(source_bytes)
        job.source_path = str(source_path)
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job

    def get_by_id(self, job_id: int) -> GenerationJob | None:
        return self._db.get(GenerationJob, job_id)

    def get_by_qr_hash(self, qr_hash: str) -> GenerationJob | None:
        return self._db.query(GenerationJob).filter(GenerationJob.qr_hash == qr_hash).first()

    def get_completed_by_qr_hash(self, qr_hash: str) -> GenerationJob | None:
        return self._db.query(GenerationJob).filter(GenerationJob.qr_hash == qr_hash, GenerationJob.status == "completed").first()

    def release_connection(self) -> None:
        self._db.rollback()

    def save(self, job: GenerationJob) -> GenerationJob:
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job
