from photoframe_backend.infrastructure.clients import image_generation


def test_generate_image_routes_openrouter_through_llm_egress_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("ROUTING_LLM_EGRESS_URL", "http://llm-egress:8080")

    captured: dict[str, str | None] = {}

    def fake_generate_image(
        *, model: str, prompt: str, image_bytes: bytes, base_url: str | None = None, api_key: str | None = None
    ) -> bytes:
        captured["model"] = model
        captured["base_url"] = base_url
        return b"openrouter-image"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)

    result = image_generation.generate_image(
        model="openai/gpt-5-image",
        prompt="Draw this as watercolor",
        image_bytes=b"source-image",
        route_via_proxy=True,
        provider_base_url="https://openrouter.ai/",
        provider_api_key="sk-test-key",
    )

    assert result == b"openrouter-image"
    assert captured["model"] == "openai/gpt-5-image"
    assert captured["base_url"] == "http://llm-egress:8080/proxy/aHR0cHM6Ly9vcGVucm91dGVyLmFpL2FwaS92MQ"

def test_generate_image_routes_selected_openai_compatible_provider_through_llm_egress(monkeypatch) -> None:
    monkeypatch.setenv("ROUTING_LLM_EGRESS_URL", "http://llm-egress:8080")

    captured: dict[str, str | None] = {}

    def fake_generate_image(
        *, model: str, prompt: str, image_bytes: bytes, base_url: str | None = None, api_key: str | None = None
    ) -> bytes:
        captured["model"] = model
        captured["base_url"] = base_url
        captured["api_key"] = api_key
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
        provider_base_url="https://embedded.pups-labs.ru/",
        provider_api_key="sk-test-key",
    )

    assert result == b"openai-compatible-image"
    assert captured["model"] == "gpt-image-1"
    assert captured["base_url"] == "http://llm-egress:8080/proxy/aHR0cHM6Ly9lbWJlZGRlZC5wdXBzLWxhYnMucnUvdjE"
    assert captured["api_key"] == "sk-test-key"


def test_generate_image_keeps_direct_transport_when_routing_disabled(monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    def fake_generate_image(
        *, model: str, prompt: str, image_bytes: bytes, base_url: str | None = None, api_key: str | None = None
    ) -> bytes:
        captured["base_url"] = base_url
        return b"openrouter-image"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openrouter_client.generate_image", fake_generate_image)

    result = image_generation.generate_image(
        model="openai/gpt-5-image",
        prompt="Draw this as watercolor",
        image_bytes=b"source-image",
        route_via_proxy=False,
        provider_base_url="https://openrouter.ai/",
        provider_api_key="sk-test-key",
    )

    assert result == b"openrouter-image"
    assert captured["base_url"] == "https://openrouter.ai/api/v1"


def test_generate_image_uses_selected_provider_directly_when_routing_disabled(monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    def fake_generate_image(
        *, model: str, prompt: str, image_bytes: bytes, base_url: str | None = None, api_key: str | None = None
    ) -> bytes:
        captured["model"] = model
        captured["base_url"] = base_url
        captured["api_key"] = api_key
        return b"openai-compatible-image"

    monkeypatch.setattr(
        "photoframe_backend.infrastructure.clients.openai_compatible_client.generate_image",
        fake_generate_image,
    )
    monkeypatch.setattr(
        "photoframe_backend.infrastructure.clients.openrouter_client.generate_image",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("openrouter client must not be used when provider is selected in site settings")),
    )

    result = image_generation.generate_image(
        model="gpt-image-1",
        prompt="Draw this as watercolor",
        image_bytes=b"source-image",
        route_via_proxy=False,
        provider_base_url="https://embedded.pups-labs.ru/",
        provider_api_key="sk-test-key",
    )

    assert result == b"openai-compatible-image"
    assert captured["model"] == "gpt-image-1"
    assert captured["base_url"] == "https://embedded.pups-labs.ru/v1"
    assert captured["api_key"] == "sk-test-key"
