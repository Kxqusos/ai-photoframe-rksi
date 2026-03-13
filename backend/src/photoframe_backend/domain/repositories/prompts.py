from collections.abc import Sequence
from typing import Protocol

from photoframe_backend.infrastructure.db.models import Prompt


class PromptRepository(Protocol):
    def get_by_id(self, prompt_id: int) -> Prompt | None: ...

    def list_by_room_id(self, room_id: int) -> Sequence[Prompt]: ...
