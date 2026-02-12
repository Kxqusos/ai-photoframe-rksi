from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ModelSetting
from app.schemas import ModelSettingIn, ModelSettingOut

DEFAULT_MODEL_NAME = "openai/gpt-5-image"
LEGACY_MODEL_NAME = "google/gemini-2.5-flash-image-preview"
LEGACY_OPENAI_MODEL_NAME = "openai/gpt-image-1"
LEGACY_MINI_MODEL_NAME = "openai/gpt-5-image-mini"

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create_setting(db: Session) -> ModelSetting:
    setting = db.get(ModelSetting, 1)
    if setting is None:
        setting = ModelSetting(id=1, model_name=DEFAULT_MODEL_NAME)
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting

    model_name = setting.model_name.strip()
    if not model_name or model_name in {LEGACY_MODEL_NAME, LEGACY_OPENAI_MODEL_NAME, LEGACY_MINI_MODEL_NAME}:
        setting.model_name = DEFAULT_MODEL_NAME
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return setting


@router.get("/model", response_model=ModelSettingOut)
def get_model(db: Session = Depends(get_db)) -> ModelSetting:
    return _get_or_create_setting(db)


@router.put("/model", response_model=ModelSettingOut)
def set_model(payload: ModelSettingIn, db: Session = Depends(get_db)) -> ModelSetting:
    setting = db.get(ModelSetting, 1)
    if setting is None:
        setting = ModelSetting(id=1, model_name=payload.model_name)
    else:
        setting.model_name = payload.model_name
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
