from collections.abc import Sequence
from typing import Protocol

from photoframe_backend.infrastructure.db.models import Room


class RoomRepository(Protocol):
    def get_by_id(self, room_id: int) -> Room | None: ...

    def get_by_slug(self, room_slug: str, *, active_only: bool) -> Room | None: ...

    def list_active(self) -> Sequence[Room]: ...

    def create_default_room(self, *, slug: str, name: str, model_name: str) -> Room: ...
