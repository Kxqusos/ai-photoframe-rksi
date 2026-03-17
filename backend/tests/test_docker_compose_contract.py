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
    assert "path: deploy/env/backend.env" in root_compose
    assert "required: false" in root_compose


def test_root_compose_runs_backend_without_reload_reloader() -> None:
    root_compose = _read("docker-compose.yml")

    assert 'BACKEND_RELOAD: "false"' in root_compose


def test_root_compose_does_not_derive_backend_runtime_env_from_host_shell() -> None:
    root_compose = _read("docker-compose.yml")

    assert "${APP__ENV" not in root_compose
    assert "${DB__HOST" not in root_compose
    assert "${DB__PORT" not in root_compose
    assert "${DB__NAME" not in root_compose
    assert "${DB__USER" not in root_compose
    assert "${DB__PASSWORD" not in root_compose
    assert "APP__ENV: docker" in root_compose
    assert "DB__HOST: postgres" in root_compose


def test_root_compose_reads_optional_backend_env_file_for_local_secrets() -> None:
    root_compose = _read("docker-compose.yml")

    assert "path: backend/.env" in root_compose
    assert "required: false" in root_compose


def test_root_compose_does_not_hardcode_placeholder_openrouter_api_key() -> None:
    root_compose = _read("docker-compose.yml")

    assert "OPENROUTER__API_KEY: your_openrouter_api_key" not in root_compose


def test_root_compose_declares_llm_egress_and_xray_client_services() -> None:
    root_compose = _read("docker-compose.yml")

    assert "\n  llm-egress:\n" in root_compose
    assert "\n  xray-client:\n" in root_compose


def test_root_compose_wires_backend_to_internal_llm_routing_services() -> None:
    root_compose = _read("docker-compose.yml")

    assert 'ROUTING_LLM_EGRESS_URL: http://llm-egress:8080' in root_compose
    assert 'ROUTING_XRAY_CLIENT_URL: http://xray-client:8081' in root_compose
