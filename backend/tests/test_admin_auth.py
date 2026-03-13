from fastapi.testclient import TestClient

from photoframe_backend.main import app


def _configure_admin_credentials(monkeypatch) -> tuple[str, str]:
    from photoframe_backend.api.http.security import settings

    username = "admin"
    password = "super-secret-password"

    monkeypatch.setattr(settings.auth, "admin_username", username)
    monkeypatch.setattr(settings.auth, "admin_password", password)
    monkeypatch.setattr(settings.auth, "jwt_secret", "test-jwt-secret-with-at-least-32-bytes")
    monkeypatch.setattr(settings.auth, "jwt_expire_minutes", 60)

    return username, password


def test_auth_service_verifies_credentials_and_issues_token() -> None:
    from photoframe_backend.application.services.auth_service import AuthService

    service = AuthService(
        admin_username="admin",
        admin_password="super-secret-password",
        jwt_secret="test-jwt-secret-with-at-least-32-bytes",
        jwt_expire_minutes=60,
    )

    assert service.verify_admin_credentials("admin", "super-secret-password") is True
    assert service.verify_admin_credentials("admin", "wrong-password") is False

    token = service.create_access_token("admin")
    payload = service.decode_access_token(token)
    assert payload["sub"] == "admin"


def test_admin_login_returns_jwt_for_valid_credentials(monkeypatch) -> None:
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)

    response = client.post("/api/admin/auth/login", json={"username": username, "password": password})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_admin_login_rejects_invalid_credentials(monkeypatch) -> None:
    username, _ = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)

    response = client.post("/api/admin/auth/login", json={"username": username, "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_admin_protected_endpoint_requires_valid_bearer_token(monkeypatch) -> None:
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)

    no_token_response = client.get("/api/admin/auth/me")
    assert no_token_response.status_code == 401

    invalid_token_response = client.get("/api/admin/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})
    assert invalid_token_response.status_code == 401

    login = client.post("/api/admin/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]

    valid_response = client.get("/api/admin/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert valid_response.status_code == 200
    assert valid_response.json()["username"] == username


def test_admin_login_rejects_when_admin_password_is_not_configured(monkeypatch) -> None:
    from photoframe_backend.api.http.security import settings

    monkeypatch.setattr(settings.auth, "admin_username", "admin")
    monkeypatch.setattr(settings.auth, "admin_password", "")
    monkeypatch.setattr(settings.auth, "jwt_secret", "test-jwt-secret-with-at-least-32-bytes")
    monkeypatch.setattr(settings.auth, "jwt_expire_minutes", 60)

    client = TestClient(app)
    response = client.post("/api/admin/auth/login", json={"username": "admin", "password": "any-password"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_admin_auth_module_does_not_expose_password_hash_context() -> None:
    import photoframe_backend.api.http.security as auth_module

    assert not hasattr(auth_module, "password_context")
