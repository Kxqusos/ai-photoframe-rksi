from typing import Annotated

from fastapi import Depends, Path as FastapiPath
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db import get_db
from app.hash_utils import PUBLIC_ID_PATTERN

DbSession = Annotated[Session, Depends(get_db)]
AdminUsername = Annotated[str, Depends(require_admin)]
PublicIdPath = Annotated[str, FastapiPath(pattern=PUBLIC_ID_PATTERN)]

__all__ = ["AdminUsername", "DbSession", "PublicIdPath", "get_db", "require_admin"]
