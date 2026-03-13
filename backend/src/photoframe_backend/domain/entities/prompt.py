from dataclasses import dataclass


@dataclass(slots=True)
class PromptEntity:
    id: int
    room_id: int
    name: str
    description: str
    prompt: str
    preview_image_url: str
    icon_image_url: str
