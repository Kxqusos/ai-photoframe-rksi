from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from photoframe_backend.shared.constants import (
    BACKEND_DIR,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_APP_ENV,
    DEFAULT_APP_NAME,
    DEFAULT_DB_HOST,
    DEFAULT_DB_NAME,
    DEFAULT_DB_PASSWORD,
    DEFAULT_DB_PORT,
    DEFAULT_DB_USER,
    DEFAULT_JWT_EXPIRE_MINUTES,
    DEFAULT_JWT_SECRET,
    DEFAULT_LOG_FILE_PATH,
    DEFAULT_LOG_LEVEL,
    DEFAULT_OPENROUTER_HTTP_REFERER,
    DEFAULT_OPENROUTER_JPEG_QUALITY,
    DEFAULT_OPENROUTER_MISSING_IMAGE_RETRIES,
    DEFAULT_OPENROUTER_PREFERRED_MAX_LATENCY,
    DEFAULT_OPENROUTER_PROVIDER_SORT,
    DEFAULT_OPENROUTER_RESULT_FORMAT,
    DEFAULT_OPENROUTER_SOURCE_JPEG_QUALITY,
    DEFAULT_OPENROUTER_SOURCE_MAX_SIDE,
    DEFAULT_OPENROUTER_X_TITLE,
    DEFAULT_PUBLIC_ROOM_SLUG,
    DEFAULT_RESULT_RETENTION_DAYS,
    DEFAULT_STORAGE_MEDIA_DIR,
)


class AppSettings(BaseModel):
    name: str = DEFAULT_APP_NAME
    env: str = DEFAULT_APP_ENV
    default_public_room_slug: str = DEFAULT_PUBLIC_ROOM_SLUG


class AuthSettings(BaseModel):
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_expire_minutes: int = DEFAULT_JWT_EXPIRE_MINUTES
    admin_username: str = DEFAULT_ADMIN_USERNAME
    admin_password: str = DEFAULT_ADMIN_PASSWORD


class DatabaseSettings(BaseModel):
    host: str = DEFAULT_DB_HOST
    port: int = DEFAULT_DB_PORT
    name: str = DEFAULT_DB_NAME
    user: str = DEFAULT_DB_USER
    password: str = DEFAULT_DB_PASSWORD
    echo: bool = False

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class LogSettings(BaseModel):
    level: str = DEFAULT_LOG_LEVEL
    file_path: str = str(DEFAULT_LOG_FILE_PATH.relative_to(BACKEND_DIR))


class OpenRouterSettings(BaseModel):
    http_referer: str = DEFAULT_OPENROUTER_HTTP_REFERER
    x_title: str = DEFAULT_OPENROUTER_X_TITLE
    provider_sort: str = DEFAULT_OPENROUTER_PROVIDER_SORT
    preferred_max_latency: int = DEFAULT_OPENROUTER_PREFERRED_MAX_LATENCY
    source_max_side: int = DEFAULT_OPENROUTER_SOURCE_MAX_SIDE
    source_jpeg_quality: int = DEFAULT_OPENROUTER_SOURCE_JPEG_QUALITY
    missing_image_retries: int = DEFAULT_OPENROUTER_MISSING_IMAGE_RETRIES
    result_format: str = DEFAULT_OPENROUTER_RESULT_FORMAT
    jpeg_quality: int = DEFAULT_OPENROUTER_JPEG_QUALITY


class StorageSettings(BaseModel):
    media_dir: str = DEFAULT_STORAGE_MEDIA_DIR
    result_retention_days: int = DEFAULT_RESULT_RETENTION_DAYS


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    openrouter: OpenRouterSettings = Field(default_factory=OpenRouterSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)

    @property
    def app_name(self) -> str:
        return self.app.name

    @property
    def jwt_secret(self) -> str:
        return self.auth.jwt_secret

    @property
    def jwt_expire_minutes(self) -> int:
        return self.auth.jwt_expire_minutes

    @property
    def admin_username(self) -> str:
        return self.auth.admin_username

    @property
    def admin_password(self) -> str:
        return self.auth.admin_password

    @property
    def log_file_path(self) -> Path:
        candidate = Path(self.log.file_path).expanduser()
        if candidate.is_absolute():
            return candidate
        return (BACKEND_DIR / candidate).resolve()

    @property
    def database_url(self) -> str:
        return self.db.database_url
