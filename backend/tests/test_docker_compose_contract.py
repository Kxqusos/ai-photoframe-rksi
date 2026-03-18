from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text()


def test_root_compose_is_standalone_and_does_not_extend_dev_file() -> None:
    root_compose = _read("docker-compose.yml")

    assert "extends:" not in root_compose
    assert "deploy/compose/docker-compose.dev.yml" not in root_compose


def test_secondary_compose_entrypoints_are_removed() -> None:
    assert not (REPO_ROOT / "deploy/compose/docker-compose.dev.yml").exists()
    assert not (REPO_ROOT / "deploy/compose/docker-compose.prod.yml").exists()


def test_root_compose_declares_fixed_project_name() -> None:
    root_compose = _read("docker-compose.yml")

    assert root_compose.startswith("name: ai_photoframe\n")


def test_root_compose_uses_explicit_backend_storage_volume_name() -> None:
    expected = "backend_storage:\n    name: ai_photoframe_backend_storage"

    root_compose = _read("docker-compose.yml")

    assert expected in root_compose


def test_root_compose_uses_explicit_postgres_volume_name() -> None:
    expected = "postgres_data:\n    name: ai_photoframe_postgres_data"

    root_compose = _read("docker-compose.yml")

    assert expected in root_compose

def test_root_compose_env_files_are_optional() -> None:
    root_compose = _read("docker-compose.yml")

    assert "path: deploy/env/postgres.env" in root_compose
    assert "required: false" in root_compose


def test_root_compose_runs_backend_without_reload_reloader() -> None:
    root_compose = _read("docker-compose.yml")

    assert 'BACKEND_RELOAD: "false"' in root_compose


def test_root_compose_uses_backend_dotenv_as_primary_backend_env_source() -> None:
    root_compose = _read("docker-compose.yml")

    assert "path: backend/.env" in root_compose
    assert 'APP__ENV: docker' not in root_compose
    assert 'APP__NAME: AI Photoframe API' not in root_compose
    assert 'DB__HOST: postgres' not in root_compose
    assert 'DB__PORT: "5432"' not in root_compose
    assert 'DB__NAME: photoframe' not in root_compose
    assert 'DB__USER: photoframe' not in root_compose
    assert 'DB__PASSWORD: photoframe' not in root_compose
    assert 'AUTH__ADMIN_USERNAME: admin' not in root_compose


def test_root_compose_keeps_only_runtime_container_wiring_in_backend_environment_block() -> None:
    root_compose = _read("docker-compose.yml")

    assert 'ROUTING_LLM_EGRESS_URL: http://llm-egress:8080' in root_compose
    assert 'ROUTING_XRAY_CLIENT_URL: http://xray-client:8081' in root_compose
    assert 'BACKEND_RELOAD: "false"' in root_compose
    assert 'BACKEND_PORT: "8000"' in root_compose


def test_root_compose_does_not_hardcode_placeholder_openrouter_api_key() -> None:
    root_compose = _read("docker-compose.yml")

    assert "OPENROUTER__API_KEY: your_openrouter_api_key" not in root_compose


def test_root_compose_does_not_hardcode_admin_secret_defaults_that_override_env_files() -> None:
    root_compose = _read("docker-compose.yml")

    assert "AUTH__JWT_SECRET: replace-me" not in root_compose
    assert "AUTH__ADMIN_PASSWORD: change-me" not in root_compose


def test_root_compose_declares_llm_egress_and_xray_client_services() -> None:
    root_compose = _read("docker-compose.yml")

    assert "\n  llm-egress:\n" in root_compose
    assert "\n  xray-client:\n" in root_compose


def test_root_compose_wires_backend_to_internal_llm_routing_services() -> None:
    root_compose = _read("docker-compose.yml")

    assert 'ROUTING_LLM_EGRESS_URL: http://llm-egress:8080' in root_compose
    assert 'ROUTING_XRAY_CLIENT_URL: http://xray-client:8081' in root_compose
