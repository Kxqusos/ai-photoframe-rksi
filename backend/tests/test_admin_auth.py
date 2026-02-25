from fastapi.testclient import TestClient

from app.main import app


def _configure_admin_credentials(monkeypatch) -> tuple[str, str]:
    from app.auth import password_context, settings

    username = "admin"
    password = "super-secret-password"
    password_hash = password_context.hash(password)

    monkeypatch.setattr(settings, "admin_username", username)
    monkeypatch.setattr(settings, "admin_password_hash", password_hash)
    monkeypatch.setattr(settings, "admin_password", "")
    monkeypatch.setattr(settings, "jwt_secret", "test-jwt-secret-with-at-least-32-bytes")
    monkeypatch.setattr(settings, "jwt_expire_minutes", 60)

    return username, password


def _configure_admin_plain_password(monkeypatch) -> tuple[str, str]:
    from app.auth import settings

    username = "admin"
    password = "plain-password-123"

    monkeypatch.setattr(settings, "admin_username", username)
    monkeypatch.setattr(settings, "admin_password", password)
    monkeypatch.setattr(settings, "admin_password_hash", "")
    monkeypatch.setattr(settings, "jwt_secret", "test-jwt-secret-with-at-least-32-bytes")
    monkeypatch.setattr(settings, "jwt_expire_minutes", 60)

    return username, password


def test_admin_login_returns_jwt_for_valid_credentials(monkeypatch) -> None:
    username, password = _configure_admin_credentials(monkeypatch)
    client = TestClient(app)

    response = client.post("/api/admin/auth/login", json={"username": username, "password": password})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_admin_login_returns_jwt_for_valid_plain_password(monkeypatch) -> None:
    username, password = _configure_admin_plain_password(monkeypatch)
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
