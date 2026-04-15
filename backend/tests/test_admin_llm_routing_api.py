from fastapi.testclient import TestClient

from photoframe_backend.infrastructure.db.base import Base
from photoframe_backend.infrastructure.db.session import engine
from photoframe_backend.main import app


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _configure_admin_credentials(monkeypatch) -> tuple[str, str]:
    from photoframe_backend.api.http.security import settings

    username = "admin"
    password = "super-secret-password"

    monkeypatch.setattr(settings.auth, "admin_username", username)
    monkeypatch.setattr(settings.auth, "admin_password", password)
    monkeypatch.setattr(settings.auth, "jwt_secret", "test-jwt-secret-with-at-least-32-bytes")
    monkeypatch.setattr(settings.auth, "jwt_expire_minutes", 60)
    return username, password


def _get_admin_token(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/admin/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_llm_routing_admin_endpoints_require_jwt(monkeypatch) -> None:
    _reset_db()
    _configure_admin_credentials(monkeypatch)
    client = TestClient(app)

    response = client.get("/api/admin/llm-routing")
    assert response.status_code == 401


def test_llm_routing_returns_default_disabled_state(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)

    response = client.get("/api/admin/llm-routing", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "status": "disabled",
        "vless_uri": "",
        "provider_base_url": "https://openrouter.ai/api/v1",
        "provider_api_key": "",
        "custom_providers": [],
        "last_error": None,
        "last_checked_at": None,
        "last_applied_at": None,
    }


def test_llm_provider_config_saves_independently_from_vless(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(
        "photoframe_backend.application.services.llm_routing.apply_vless_uri",
        lambda vless_uri: (_ for _ in ()).throw(AssertionError("vless apply must not run when saving provider config")),
    )
    monkeypatch.setattr(
        "photoframe_backend.application.services.llm_routing.probe_provider_base_url",
        lambda provider_base_url: (_ for _ in ()).throw(AssertionError("provider probe must not run when saving provider config")),
    )

    response = client.put(
        "/api/admin/llm-routing/provider",
        headers=headers,
        json={
            "provider_base_url": "https://embedded.pups-labs.ru/",
            "provider_api_key": "sk-test-key",
            "custom_providers": [{"base_url": "https://embedded.pups-labs.ru/", "api_key": "sk-test-key"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["vless_uri"] == ""
    assert response.json()["provider_base_url"] == "https://embedded.pups-labs.ru/v1"
    assert response.json()["provider_api_key"] == "sk-test-key"
    assert response.json()["custom_providers"] == [{"base_url": "https://embedded.pups-labs.ru/v1", "api_key": "sk-test-key"}]
    assert response.json()["status"] == "disabled"
    assert response.json()["last_error"] is None


def test_llm_routing_saves_vless_uri_and_marks_error_when_apply_or_probe_fails(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(
        "photoframe_backend.application.services.llm_routing.apply_vless_uri",
        lambda vless_uri: (True, None),
    )
    monkeypatch.setattr(
        "photoframe_backend.application.services.llm_routing.probe_provider_base_url",
        lambda provider_base_url: (False, "probe timeout"),
    )

    response = client.put(
        "/api/admin/llm-routing/config",
        headers=headers,
        json={"vless_uri": "vless://uuid@example.com:443?security=reality&pbk=test&fp=chrome&sni=example.com&type=tcp"},
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is False
    assert response.json()["status"] == "error"
    assert response.json()["vless_uri"].startswith("vless://uuid@example.com:443")
    assert response.json()["provider_base_url"] == "https://openrouter.ai/api/v1"
    assert response.json()["provider_api_key"] == ""
    assert response.json()["custom_providers"] == []
    assert response.json()["last_error"] == "probe timeout"
    assert response.json()["last_checked_at"] is not None
    assert response.json()["last_applied_at"] is not None


def test_llm_routing_can_enable_only_after_successful_apply_and_probe(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(
        "photoframe_backend.application.services.llm_routing.apply_vless_uri",
        lambda vless_uri: (True, None),
    )
    monkeypatch.setattr(
        "photoframe_backend.application.services.llm_routing.probe_provider_base_url",
        lambda provider_base_url: (True, None),
    )

    saved = client.put(
        "/api/admin/llm-routing/config",
        headers=headers,
        json={"vless_uri": "vless://uuid@example.com:443?security=reality&pbk=test&fp=chrome&sni=example.com&type=tcp"},
    )
    assert saved.status_code == 200
    assert saved.json()["status"] == "disabled"

    enabled = client.post(
        "/api/admin/llm-routing/toggle",
        headers=headers,
        json={"enabled": True},
    )
    assert enabled.status_code == 200
    assert enabled.json()["enabled"] is True
    assert enabled.json()["status"] == "active"
    assert enabled.json()["last_error"] is None


def test_llm_routing_test_probes_selected_provider_base_url(monkeypatch) -> None:
    _reset_db()
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)
    token = _get_admin_token(client, username, password)
    headers = {"Authorization": f"Bearer {token}"}
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        "photoframe_backend.application.services.llm_routing.apply_vless_uri",
        lambda vless_uri: (True, None),
    )

    def fake_probe(provider_base_url: str) -> tuple[bool, str | None]:
        captured["provider_base_url"] = provider_base_url
        return True, None

    monkeypatch.setattr("photoframe_backend.application.services.llm_routing.probe_provider_base_url", fake_probe)

    saved = client.put(
        "/api/admin/llm-routing/provider",
        headers=headers,
        json={
            "provider_base_url": "https://embedded.pups-labs.ru/",
            "provider_api_key": "sk-test-key",
            "custom_providers": [{"base_url": "https://embedded.pups-labs.ru/", "api_key": "sk-test-key"}],
        },
    )
    assert saved.status_code == 200

    saved = client.put(
        "/api/admin/llm-routing/config",
        headers=headers,
        json={"vless_uri": "vless://uuid@example.com:443?security=reality&pbk=test&fp=chrome&sni=example.com&type=tcp"},
    )
    assert saved.status_code == 200

    tested = client.post("/api/admin/llm-routing/test", headers=headers)
    assert tested.status_code == 200
    assert captured["provider_base_url"] == "https://embedded.pups-labs.ru/v1"
    assert tested.json()["status"] == "disabled"
