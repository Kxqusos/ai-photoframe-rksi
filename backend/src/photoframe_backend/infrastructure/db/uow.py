from collections.abc import Callable

from sqlalchemy.orm import Session

from photoframe_backend.infrastructure.db.session import SessionLocal


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.session is None:
            return
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()
