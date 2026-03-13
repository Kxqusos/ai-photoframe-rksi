from collections.abc import Sequence

from sqlalchemy.orm import Session

from photoframe_backend.infrastructure.db.models import Prompt


class SqlAlchemyPromptRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, prompt_id: int) -> Prompt | None:
        return self._db.get(Prompt, prompt_id)

    def list_by_room_id(self, room_id: int) -> Sequence[Prompt]:
        return self._db.query(Prompt).filter(Prompt.room_id == room_id).order_by(Prompt.id.asc()).all()
