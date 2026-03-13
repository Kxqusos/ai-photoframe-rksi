from dataclasses import dataclass


@dataclass(slots=True)
class RoomEntity:
    id: int
    slug: str
    name: str
    model_name: str
    is_active: bool
