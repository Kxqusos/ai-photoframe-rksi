from pathlib import Path

import pytest

from photoframe_backend.infrastructure.settings.runtime import load_settings


@pytest.fixture(autouse=True)
def clear_settings_env(monkeypatch) -> None:
    keys = [
        "APP__NAME",
        "APP__ENV",
        "APP__DEFAULT_PUBLIC_ROOM_SLUG",
        "AUTH__JWT_SECRET",
        "AUTH__JWT_EXPIRE_MINUTES",
        "AUTH__ADMIN_USERNAME",
        "AUTH__ADMIN_PASSWORD",
        "DB__HOST",
        "DB__PORT",
        "DB__NAME",
        "DB__USER",
        "DB__PASSWORD",
        "DB__ECHO",
        "LOG__FILE_PATH",
        "LOG__LEVEL",
        "OPENROUTER__API_KEY",
        "OPENROUTER__HTTP_REFERER",
        "OPENROUTER__X_TITLE",
        "OPENROUTER__PROVIDER_SORT",
        "OPENROUTER__PREFERRED_MAX_LATENCY",
        "OPENROUTER__SOURCE_MAX_SIDE",
        "OPENROUTER__SOURCE_JPEG_QUALITY",
        "OPENROUTER__MISSING_IMAGE_RETRIES",
        "OPENROUTER__RESULT_FORMAT",
        "OPENROUTER__JPEG_QUALITY",
        "STORAGE__MEDIA_DIR",
        "STORAGE__RESULT_RETENTION_DAYS",
        "APP_NAME",
        "JWT_SECRET",
        "JWT_EXPIRE_MINUTES",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "LOG_FILE_PATH",
        "LOG_LEVEL",
        "OPENROUTER_API_KEY",
        "OPENROUTER_HTTP_REFERER",
        "OPENROUTER_X_TITLE",
        "OPENROUTER_PROVIDER_SORT",
        "OPENROUTER_PREFERRED_MAX_LATENCY",
        "OPENROUTER_SOURCE_MAX_SIDE",
        "OPENROUTER_SOURCE_JPEG_QUALITY",
        "OPENROUTER_MISSING_IMAGE_RETRIES",
        "OPENROUTER_RESULT_FORMAT",
        "OPENROUTER_JPEG_QUALITY",
        "RESULT_RETENTION_DAYS",
        "DEFAULT_PUBLIC_ROOM_SLUG",
        "DATABASE_URL",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_load_settings_reads_grouped_values_from_env_file(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "APP__NAME=Photo API",
                "APP__ENV=development",
                "APP__DEFAULT_PUBLIC_ROOM_SLUG=zzzzzzzz",
                "AUTH__JWT_SECRET=super-secret",
                "AUTH__ADMIN_PASSWORD=super-admin",
                "DB__HOST=postgres.internal",
                "DB__PORT=5433",
                "DB__NAME=photoframe_dev",
                "OPENROUTER__API_KEY=file-key",
                "STORAGE__RESULT_RETENTION_DAYS=14",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    for key in [
        "APP__NAME",
        "APP__ENV",
        "APP__DEFAULT_PUBLIC_ROOM_SLUG",
        "AUTH__JWT_SECRET",
        "AUTH__ADMIN_PASSWORD",
        "DB__HOST",
        "DB__PORT",
        "DB__NAME",
        "OPENROUTER__API_KEY",
        "STORAGE__RESULT_RETENTION_DAYS",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = load_settings(env_path=env_path, allow_test_defaults=False)

    assert settings.app.name == "Photo API"
    assert settings.app.default_public_room_slug == "zzzzzzzz"
    assert settings.auth.jwt_secret == "super-secret"
    assert settings.auth.admin_password == "super-admin"
    assert settings.db.host == "postgres.internal"
    assert settings.db.port == 5433
    assert settings.db.name == "photoframe_dev"
    assert settings.openrouter.api_key == "file-key"
    assert settings.storage.result_retention_days == 14


def test_load_settings_prefers_process_env_over_env_file(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "APP__NAME=From File",
                "AUTH__JWT_SECRET=file-secret",
                "AUTH__ADMIN_PASSWORD=file-admin",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("APP__NAME", "From Env")
    monkeypatch.setenv("AUTH__JWT_SECRET", "env-secret")
    monkeypatch.setenv("AUTH__ADMIN_PASSWORD", "env-admin")

    settings = load_settings(env_path=env_path, allow_test_defaults=False)

    assert settings.app.name == "From Env"
    assert settings.auth.jwt_secret == "env-secret"
    assert settings.auth.admin_password == "env-admin"


def test_load_settings_fails_fast_for_required_secrets_outside_test_mode(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "APP__ENV=development",
                "AUTH__JWT_SECRET=change-me-in-production",
                "AUTH__ADMIN_PASSWORD=",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("AUTH__JWT_SECRET", raising=False)
    monkeypatch.delenv("AUTH__ADMIN_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="AUTH__JWT_SECRET"):
        load_settings(env_path=env_path, allow_test_defaults=False)


def test_load_settings_accepts_legacy_env_names_when_grouped_values_absent(monkeypatch) -> None:
    monkeypatch.setenv("LOG_FILE_PATH", "logs/legacy.log")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("JWT_SECRET", "legacy-secret")
    monkeypatch.setenv("ADMIN_PASSWORD", "legacy-admin")

    settings = load_settings(allow_test_defaults=False)

    assert settings.log.file_path == "logs/legacy.log"
    assert settings.log.level == "DEBUG"
    assert settings.auth.jwt_secret == "legacy-secret"
    assert settings.auth.admin_password == "legacy-admin"


def test_legacy_process_env_overrides_grouped_file_values(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "AUTH__JWT_SECRET=file-secret",
                "AUTH__ADMIN_PASSWORD=file-admin",
                "LOG__LEVEL=WARNING",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("JWT_SECRET", "legacy-secret")
    monkeypatch.setenv("ADMIN_PASSWORD", "legacy-admin")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = load_settings(env_path=env_path, allow_test_defaults=False)

    assert settings.auth.jwt_secret == "legacy-secret"
    assert settings.auth.admin_password == "legacy-admin"
    assert settings.log.level == "DEBUG"
