from fastapi.testclient import TestClient

from photoframe_backend.main import app


def test_src_entrypoint_exposes_app():
    from photoframe_backend.main import app as src_app

    assert src_app is app


def test_src_entrypoint_bootstraps_default_room_on_startup(monkeypatch):
    import photoframe_backend.main as main_module

    called = False

    def fake_bootstrap_default_room(*, engine, database_url: str, default_room_slug: str) -> None:
        nonlocal called
        assert database_url
        assert default_room_slug
        called = True

    monkeypatch.setattr(main_module, "bootstrap_default_room", fake_bootstrap_default_room)

    with TestClient(main_module.app):
        pass

    assert called is True


def test_healthcheck_returns_ok():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
