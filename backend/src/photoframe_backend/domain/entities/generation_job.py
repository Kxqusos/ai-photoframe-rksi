from dataclasses import dataclass


@dataclass(slots=True)
class GenerationJobEntity:
    id: int
    prompt_id: int
    room_id: int
    status: str
    qr_hash: str | None
    source_path: str | None
    result_path: str | None
    error_message: str | None
