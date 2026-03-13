from collections.abc import Sequence

from photoframe_backend.domain.repositories.prompts import PromptRepository
from photoframe_backend.infrastructure.db.models import Prompt


class PromptService:
    def __init__(self, prompt_repository: PromptRepository) -> None:
        self._prompt_repository = prompt_repository

    def get_prompt(self, prompt_id: int) -> Prompt | None:
        return self._prompt_repository.get_by_id(prompt_id)

    def list_prompts_for_room(self, room_id: int) -> Sequence[Prompt]:
        return self._prompt_repository.list_by_room_id(room_id)
