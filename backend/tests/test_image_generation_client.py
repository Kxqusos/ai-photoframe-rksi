import base64
from io import BytesIO

import pytest
from PIL import Image

from photoframe_backend.infrastructure.clients import image_generation, openai_compatible_client


class _FakeImageResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def model_dump(self) -> dict:
        return self._payload


class _FakeImagesAPI:
    def __init__(self, calls: list[dict], payload: dict) -> None:
        self._calls = calls
        self._payload = payload

    def edit(self, **kwargs):
        self._calls.append(kwargs)
        return _FakeImageResponse(self._payload)


class _FakeOpenAIClient:
    def __init__(self, calls: list[dict], payload: dict) -> None:
        self.images = _FakeImagesAPI(calls, payload)


def _one_pixel_png() -> bytes:
    output = BytesIO()
    Image.new("RGBA", (1, 1), color=(120, 160, 200, 255)).save(output, format="PNG")
    return output.getvalue()


def test_generate_image_uses_openai_compatible_client_when_provider_matches(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "https://embedded.pups-labs.ru/")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "compatible-test-key")

    captured: dict[str, str] = {}

    def fake_generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
        captured["model"] = model
        captured["prompt"] = prompt
        captured["image_bytes"] = image_bytes.decode("utf-8")
        return b"compatible-image"

    monkeypatch.setattr("photoframe_backend.infrastructure.clients.openai_compatible_client.generate_image", fake_generate_image)
    monkeypatch.setattr(
        "photoframe_backend.infrastructure.clients.openrouter_client.generate_image",
        lambda **kwargs: pytest.fail("openrouter client should not be used when provider is openai_compatible"),
    )

    result = image_generation.generate_image(
        model="gpt-image-1",
        prompt="Draw this as watercolor",
        image_bytes=b"source-image",
    )

    assert result == b"compatible-image"
    assert captured == {
        "model": "gpt-image-1",
        "prompt": "Draw this as watercolor",
        "image_bytes": "source-image",
    }


def test_openai_compatible_client_uses_images_edit_api_and_normalizes_base_url(monkeypatch) -> None:
    init_calls: list[dict] = []
    edit_calls: list[dict] = []
    encoded = base64.b64encode(_one_pixel_png()).decode("utf-8")

    def fake_openai(**kwargs):
        init_calls.append(kwargs)
        return _FakeOpenAIClient(
            edit_calls,
            payload={"data": [{"b64_json": encoded}]},
        )

    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "https://embedded.pups-labs.ru/")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "compatible-test-key")
    monkeypatch.setattr(
        "photoframe_backend.infrastructure.clients.openai_compatible_client._load_openai_client_class",
        lambda: fake_openai,
    )

    result = openai_compatible_client.generate_image(
        model="gpt-image-1",
        prompt="Make it cinematic",
        image_bytes=b"source-image",
    )

    assert result.startswith(b"\xff\xd8\xff")
    assert len(init_calls) == 1
    assert len(edit_calls) == 1
    assert init_calls[0]["api_key"] == "compatible-test-key"
    assert init_calls[0]["base_url"] == "https://embedded.pups-labs.ru/v1"
    assert edit_calls[0]["model"] == "gpt-image-1"
    assert edit_calls[0]["prompt"] == "Make it cinematic"


def test_generate_image_defaults_to_openrouter(monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-test-key")

    monkeypatch.setattr(
        "photoframe_backend.infrastructure.clients.openai_compatible_client.generate_image",
        lambda **kwargs: pytest.fail("compatible client should not be used by default"),
    )
    monkeypatch.setattr(
        "photoframe_backend.infrastructure.clients.openrouter_client.generate_image",
        lambda **kwargs: b"openrouter-image",
    )

    result = image_generation.generate_image(
        model="openai/gpt-5-image",
        prompt="Draw this as watercolor",
        image_bytes=b"source-image",
    )

    assert result == b"openrouter-image"
