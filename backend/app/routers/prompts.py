from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Prompt
from app.schemas import PromptCreate, PromptOut

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptOut])
def list_prompts(db: Session = Depends(get_db)) -> list[Prompt]:
    return db.query(Prompt).order_by(Prompt.id.asc()).all()


@router.post("", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
def create_prompt(payload: PromptCreate, db: Session = Depends(get_db)) -> Prompt:
    row = Prompt(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
