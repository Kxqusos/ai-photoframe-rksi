import logging
from collections.abc import Callable
from pathlib import Path

from photoframe_backend.application.services.prompt_service import PromptService
from photoframe_backend.application.services.room_service import RoomService
from photoframe_backend.domain.repositories.jobs import JobRepository
from photoframe_backend.infrastructure.db.models import GenerationJob

logger = logging.getLogger(__name__)


class JobService:
    def __init__(
        self,
        *,
        room_service: RoomService | None = None,
        prompt_service: PromptService | None = None,
        job_repository: JobRepository,
        room_repository=None,
        prompt_repository=None,
        generate_qr_hash: Callable[[], str] | None = None,
        generate_image: Callable[..., bytes] | None = None,
        build_room_result_dir: Callable[[str], Path] | None = None,
        build_filename: Callable[[int, str], str] | None = None,
        resolve_result_suffix: Callable[[], str] | None = None,
        prune_result_files: Callable[[], None] | None = None,
        cleanup_source_file: Callable[[str | None], None] | None = None,
        default_model_name: str = "openai/gpt-5-image",
    ) -> None:
        self._room_service = room_service or RoomService(room_repository, default_model_name=default_model_name)
        self._prompt_service = prompt_service or PromptService(prompt_repository)
        self._job_repository = job_repository
        self._generate_qr_hash = generate_qr_hash or (lambda: "ph000000")
        self._generate_image = generate_image
        self._build_room_result_dir = build_room_result_dir
        self._build_filename = build_filename
        self._resolve_result_suffix = resolve_result_suffix
        self._prune_result_files = prune_result_files or (lambda: None)
        self._cleanup_source_file = cleanup_source_file or (lambda _path: None)
        self._default_model_name = default_model_name

    def create_processing_job(self, *, prompt_id: int, room_slug: str, source_bytes: bytes) -> GenerationJob:
        room = self._room_service.get_room_by_slug(room_slug, active_only=True)
        if room is None:
            raise ValueError("room not found")

        prompt = self._prompt_service.get_prompt(prompt_id)
        if prompt is None:
            raise ValueError("prompt not found")
        if prompt.room_id != room.id:
            raise ValueError("prompt does not belong to room")

        return self._job_repository.create_processing_job(
            prompt_id=prompt_id,
            room_id=room.id,
            source_bytes=source_bytes,
            qr_hash=self._generate_qr_hash(),
        )

    def create_processing_job_for_room_id(self, *, prompt_id: int, room_id: int, source_bytes: bytes) -> GenerationJob:
        room = self._room_service._room_repository.get_by_id(room_id)
        if room is None:
            raise ValueError("room not found")
        return self.create_processing_job(prompt_id=prompt_id, room_slug=room.slug, source_bytes=source_bytes)

    def run_generation_sync(self, job_id: int) -> GenerationJob:
        job = self._job_repository.get_by_id(job_id)
        if job is None:
            raise ValueError(f"job {job_id} not found")

        prompt = self._prompt_service.get_prompt(job.prompt_id)
        if prompt is None:
            job.status = "error"
            job.error_message = "prompt not found"
            return self._job_repository.save(job)

        room = self._room_service._room_repository.get_by_id(job.room_id)
        if room is None:
            job.status = "error"
            job.error_message = "room not found"
            return self._job_repository.save(job)

        source_path = job.source_path
        try:
            source_bytes = Path(source_path).read_bytes() if source_path else b""
            if self._generate_image is None:
                raise RuntimeError("generate_image dependency is not configured")
            if self._build_room_result_dir is None or self._build_filename is None or self._resolve_result_suffix is None:
                raise RuntimeError("storage dependencies are not configured")

            generated = self._generate_image(model=room.model_name, prompt=prompt.prompt, image_bytes=source_bytes)
            result_dir = self._build_room_result_dir(room.slug)
            result_path = result_dir / self._build_filename(job.id, self._resolve_result_suffix())
            result_path.write_bytes(generated)
            self._prune_result_files()

            job.result_path = str(result_path)
            if not job.qr_hash:
                job.qr_hash = self._generate_qr_hash()
            job.status = "completed"
            job.error_message = None
        except Exception as exc:
            logger.exception(
                "Generation job failed",
                extra={
                    "job_id": job.id,
                    "room_id": job.room_id,
                    "prompt_id": job.prompt_id,
                    "room_model_name": room.model_name,
                },
            )
            job.status = "error"
            job.error_message = str(exc)
        finally:
            self._cleanup_source_file(source_path)
            job.source_path = None

        return self._job_repository.save(job)
