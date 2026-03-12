from fastapi.testclient import TestClient

from app.main import app


def test_src_entrypoint_exposes_app():
    from photoframe_backend.main import app as src_app

    assert src_app is app


def test_src_entrypoint_runs_db_init_on_startup(monkeypatch):
    import photoframe_backend.main as main_module

    called = False

    def fake_init_db() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(main_module, "init_db", fake_init_db)

    with TestClient(main_module.app):
        pass

    assert called is True


def test_healthcheck_returns_ok():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
