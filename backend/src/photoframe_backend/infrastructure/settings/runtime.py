import os
import sys
from pathlib import Path

from photoframe_backend.infrastructure.settings.loader import load_env_file
from photoframe_backend.infrastructure.settings.models import RuntimeSettings
from photoframe_backend.shared.constants import DEFAULT_ADMIN_PASSWORD, DEFAULT_JWT_SECRET

LEGACY_TO_GROUPED_ENV = {
    "APP_NAME": "APP__NAME",
    "LLM_PROVIDER": "LLM__PROVIDER",
    "JWT_SECRET": "AUTH__JWT_SECRET",
    "JWT_EXPIRE_MINUTES": "AUTH__JWT_EXPIRE_MINUTES",
    "ADMIN_USERNAME": "AUTH__ADMIN_USERNAME",
    "ADMIN_PASSWORD": "AUTH__ADMIN_PASSWORD",
    "LOG_FILE_PATH": "LOG__FILE_PATH",
    "LOG_LEVEL": "LOG__LEVEL",
    "OPENAI_COMPATIBLE_BASE_URL": "OPENAI_COMPATIBLE__BASE_URL",
    "OPENAI_COMPATIBLE_API_KEY": "OPENAI_COMPATIBLE__API_KEY",
    "OPENROUTER_API_KEY": "OPENROUTER__API_KEY",
    "OPENROUTER_HTTP_REFERER": "OPENROUTER__HTTP_REFERER",
    "OPENROUTER_X_TITLE": "OPENROUTER__X_TITLE",
    "OPENROUTER_PROVIDER_SORT": "OPENROUTER__PROVIDER_SORT",
    "OPENROUTER_PREFERRED_MAX_LATENCY": "OPENROUTER__PREFERRED_MAX_LATENCY",
    "OPENROUTER_SOURCE_MAX_SIDE": "OPENROUTER__SOURCE_MAX_SIDE",
    "OPENROUTER_SOURCE_JPEG_QUALITY": "OPENROUTER__SOURCE_JPEG_QUALITY",
    "OPENROUTER_MISSING_IMAGE_RETRIES": "OPENROUTER__MISSING_IMAGE_RETRIES",
    "OPENROUTER_RESULT_FORMAT": "OPENROUTER__RESULT_FORMAT",
    "OPENROUTER_JPEG_QUALITY": "OPENROUTER__JPEG_QUALITY",
    "RESULT_RETENTION_DAYS": "STORAGE__RESULT_RETENTION_DAYS",
    "DEFAULT_PUBLIC_ROOM_SLUG": "APP__DEFAULT_PUBLIC_ROOM_SLUG",
}
HYDRATED_LEGACY_ENV_VALUES: dict[str, str] = {}


def _allow_test_defaults(settings: RuntimeSettings, override: bool | None) -> bool:
    if override is not None:
        return override
    return settings.app.env.lower() == "test" or "pytest" in sys.modules


def _ensure_required_secrets(settings: RuntimeSettings, allow_test_defaults: bool | None) -> None:
    if _allow_test_defaults(settings, allow_test_defaults):
        return

    missing: list[str] = []
    if settings.auth.jwt_secret.strip() == DEFAULT_JWT_SECRET:
        missing.append("AUTH__JWT_SECRET")
    if settings.auth.admin_password.strip() == DEFAULT_ADMIN_PASSWORD:
        missing.append("AUTH__ADMIN_PASSWORD")

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required secrets for non-test runtime: {joined}")


def _has_grouped_db_env() -> bool:
    return any(key.startswith("DB__") for key in os.environ)


def _hydrate_grouped_env_from_legacy(file_keys: set[str]) -> list[str]:
    hydrated_keys: list[str] = []
    for legacy_key, grouped_key in LEGACY_TO_GROUPED_ENV.items():
        legacy_value = os.getenv(legacy_key)
        if legacy_value is None:
            continue
        if HYDRATED_LEGACY_ENV_VALUES.get(legacy_key) == legacy_value:
            continue
        HYDRATED_LEGACY_ENV_VALUES.pop(legacy_key, None)
        if grouped_key in os.environ and grouped_key not in file_keys:
            continue
        os.environ[grouped_key] = legacy_value
        hydrated_keys.append(grouped_key)

    return hydrated_keys


def _hydrate_legacy_env(settings: RuntimeSettings) -> None:
    legacy_pairs = {
        "APP_NAME": settings.app_name,
        "LLM_PROVIDER": settings.llm.provider,
        "JWT_SECRET": settings.jwt_secret,
        "JWT_EXPIRE_MINUTES": str(settings.jwt_expire_minutes),
        "ADMIN_USERNAME": settings.admin_username,
        "ADMIN_PASSWORD": settings.admin_password,
        "LOG_FILE_PATH": str(settings.log_file_path),
        "LOG_LEVEL": settings.log.level,
        "OPENAI_COMPATIBLE_BASE_URL": settings.openai_compatible.base_url,
        "OPENAI_COMPATIBLE_API_KEY": settings.openai_compatible.api_key,
        "OPENROUTER_API_KEY": settings.openrouter.api_key,
        "OPENROUTER_HTTP_REFERER": settings.openrouter.http_referer,
        "OPENROUTER_X_TITLE": settings.openrouter.x_title,
        "OPENROUTER_PROVIDER_SORT": settings.openrouter.provider_sort,
        "OPENROUTER_PREFERRED_MAX_LATENCY": str(settings.openrouter.preferred_max_latency),
        "OPENROUTER_SOURCE_MAX_SIDE": str(settings.openrouter.source_max_side),
        "OPENROUTER_SOURCE_JPEG_QUALITY": str(settings.openrouter.source_jpeg_quality),
        "OPENROUTER_MISSING_IMAGE_RETRIES": str(settings.openrouter.missing_image_retries),
        "OPENROUTER_RESULT_FORMAT": settings.openrouter.result_format,
        "OPENROUTER_JPEG_QUALITY": str(settings.openrouter.jpeg_quality),
        "RESULT_RETENTION_DAYS": str(settings.storage.result_retention_days),
        "DEFAULT_PUBLIC_ROOM_SLUG": settings.app.default_public_room_slug,
    }

    if _has_grouped_db_env():
        legacy_pairs["DATABASE_URL"] = settings.database_url

    for key, value in legacy_pairs.items():
        if value == "":
            continue
        if key not in os.environ or key in HYDRATED_LEGACY_ENV_VALUES:
            os.environ[key] = value
            HYDRATED_LEGACY_ENV_VALUES[key] = value


def load_settings(env_path: Path | None = None, allow_test_defaults: bool | None = None) -> RuntimeSettings:
    _, file_keys = load_env_file(env_path)
    hydrated_keys = _hydrate_grouped_env_from_legacy(file_keys)
    try:
        settings = RuntimeSettings()
    finally:
        for key in file_keys | set(hydrated_keys):
            os.environ.pop(key, None)
    _ensure_required_secrets(settings, allow_test_defaults)
    _hydrate_legacy_env(settings)
    return settings
