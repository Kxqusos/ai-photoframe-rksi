from photoframe_backend.infrastructure.clients import image_generation


def test_generate_image_routes_openrouter_through_llm_egress_when_enabled(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("ROUTING_LLM_EGRESS_URL", "http://llm-egress:8080")

    captured: dict[str, str | None] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes, base_url: str | None = None) -> bytes:
        captured["model"] = model
        captured["base_url"] = base_url
        return b"openrouter-image"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)

    result = image_generation.generate_image(
        model="openai/gpt-5-image",
        prompt="Draw this as watercolor",
        image_bytes=b"source-image",
        route_via_proxy=True,
    )

    assert result == b"openrouter-image"
    assert captured["model"] == "openai/gpt-5-image"
    assert captured["base_url"] == "http://llm-egress:8080/proxy/aHR0cHM6Ly9vcGVucm91dGVyLmFpL2FwaS92MQ"


def test_generate_image_routes_openai_compatible_through_llm_egress_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "https://embedded.pups-labs.ru/")
    monkeypatch.setenv("ROUTING_LLM_EGRESS_URL", "http://llm-egress:8080")

    captured: dict[str, str | None] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes, base_url: str | None = None) -> bytes:
        captured["model"] = model
        captured["base_url"] = base_url
        return b"openai-compatible-image"

    monkeypatch.setattr(
        "photoframe_backend.infrastructure.clients.openai_compatible_client.generate_image",
        fake_generate_image,
    )

    result = image_generation.generate_image(
        model="gpt-image-1",
        prompt="Draw this as watercolor",
        image_bytes=b"source-image",
        route_via_proxy=True,
    )

    assert result == b"openai-compatible-image"
    assert captured["model"] == "gpt-image-1"
    assert captured["base_url"] == "http://llm-egress:8080/proxy/aHR0cHM6Ly9lbWJlZGRlZC5wdXBzLWxhYnMucnUvdjE"


def test_generate_image_keeps_direct_transport_when_routing_disabled(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    captured: dict[str, str | None] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes, base_url: str | None = None) -> bytes:
        captured["base_url"] = base_url
        return b"openrouter-image"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)

    result = image_generation.generate_image(
        model="openai/gpt-5-image",
        prompt="Draw this as watercolor",
        image_bytes=b"source-image",
        route_via_proxy=False,
    )

    assert result == b"openrouter-image"
    assert captured["base_url"] is None
