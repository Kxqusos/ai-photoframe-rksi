from collections.abc import Sequence

from photoframe_backend.domain.repositories.rooms import RoomRepository
from photoframe_backend.infrastructure.db.models import Room


class RoomService:
    def __init__(
        self,
        room_repository: RoomRepository,
        *,
        default_room_slug: str = "ph000000",
        default_room_name: str = "Main",
        default_model_name: str = "openai/gpt-5-image",
    ) -> None:
        self._room_repository = room_repository
        self._default_room_slug = default_room_slug
        self._default_room_name = default_room_name
        self._default_model_name = default_model_name

    def list_public_rooms(self) -> Sequence[Room]:
        return self._room_repository.list_active()

    def get_room_by_slug(self, room_slug: str, *, active_only: bool) -> Room | None:
        return self._room_repository.get_by_slug(room_slug, active_only=active_only)

    def get_or_create_default_room(self) -> Room:
        room = self._room_repository.get_by_slug(self._default_room_slug, active_only=False)
        if room is not None:
            return room
        return self._room_repository.create_default_room(
            slug=self._default_room_slug,
            name=self._default_room_name,
            model_name=self._default_model_name,
        )
