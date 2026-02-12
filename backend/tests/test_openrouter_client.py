import base64
from io import BytesIO

import pytest
from PIL import Image

from app import openrouter_client


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def model_dump(self) -> dict:
        return self._payload


class _FakeCompletionsAPI:
    def __init__(self, calls: list[dict], payload: dict | None = None, error: Exception | None = None) -> None:
        self._calls = calls
        self._payload = payload or {}
        self._error = error

    def create(self, **kwargs):
        self._calls.append(kwargs)
        if self._error:
            raise self._error
        return _FakeResponse(self._payload)


class _FakeOpenAIClient:
    def __init__(self, calls: list[dict], payload: dict | None = None, error: Exception | None = None) -> None:
        self.chat = type("ChatAPI", (), {"completions": _FakeCompletionsAPI(calls, payload=payload, error=error)})()


class _FakeStatusError(Exception):
    def __init__(self, status_code: int, body: dict) -> None:
        super().__init__("request failed")
        self.status_code = status_code
        self.body = body


def test_generate_image_recovers_when_openai_was_missing_during_module_import(monkeypatch) -> None:
    init_calls: list[dict] = []
    create_calls: list[dict] = []
    encoded = base64.b64encode(b"generated-after-retry").decode("utf-8")

    def fake_openai(**kwargs):
        init_calls.append(kwargs)
        return _FakeOpenAIClient(
            create_calls,
            payload={
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "image_url": {
                                        "url": f"data:image/png;base64,{encoded}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("app.openrouter_client.OpenAI", None)
    monkeypatch.setattr(
        "app.openrouter_client._load_openai_client_class",
        lambda: fake_openai,
        raising=False,
    )

    result = openrouter_client.generate_image(
        model="openai/gpt-image-1",
        prompt="Draw this in watercolor style",
        image_bytes=b"source-image",
    )

    assert result == b"generated-after-retry"
    assert len(init_calls) == 1
    assert len(create_calls) == 1


def test_generate_image_uses_openai_sdk_client_with_openrouter_base_url(monkeypatch) -> None:
    init_calls: list[dict] = []
    create_calls: list[dict] = []
    encoded = base64.b64encode(b"generated-image").decode("utf-8")

    def fake_openai(**kwargs):
        init_calls.append(kwargs)
        return _FakeOpenAIClient(
            create_calls,
            payload={
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "image_url": {
                                        "url": f"data:image/png;base64,{encoded}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_HTTP_REFERER", "https://photoframe.local")
    monkeypatch.setenv("OPENROUTER_X_TITLE", "AI Photoframe")
    monkeypatch.setattr("app.openrouter_client.OpenAI", fake_openai)

    result = openrouter_client.generate_image(
        model="openai/gpt-image-1",
        prompt="Draw this in watercolor style",
        image_bytes=b"source-image",
    )

    assert result == b"generated-image"
    assert len(init_calls) == 1
    assert len(create_calls) == 1

    init_call = init_calls[0]
    assert init_call["api_key"] == "test-key"
    assert init_call["base_url"] == openrouter_client.OPENROUTER_BASE_URL
    assert init_call["default_headers"]["HTTP-Referer"] == "https://photoframe.local"
    assert init_call["default_headers"]["X-Title"] == "AI Photoframe"

    create_call = create_calls[0]
    assert create_call["model"] == "openai/gpt-image-1"
    assert create_call["extra_body"]["modalities"] == ["image", "text"]
    assert create_call["extra_body"]["stream"] is False
    assert create_call["extra_body"]["provider"]["sort"] == "throughput"
    assert create_call["extra_body"]["provider"]["preferred_max_latency"] == 25
    content = create_call["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "Draw this in watercolor style"
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_generate_image_supports_camel_case_image_url(monkeypatch) -> None:
    encoded = base64.b64encode(b"generated-camel").decode("utf-8")

    def fake_openai(**kwargs):
        return _FakeOpenAIClient(
            [],
            payload={
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "imageUrl": {
                                        "url": f"data:image/png;base64,{encoded}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("app.openrouter_client.OpenAI", fake_openai)

    result = openrouter_client.generate_image(
        model="openai/gpt-image-1",
        prompt="Draw this in oil painting",
        image_bytes=b"source-image",
    )

    assert result == b"generated-camel"


def test_generate_image_converts_png_payload_to_jpeg(monkeypatch) -> None:
    one_pixel_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2iR4sAAAAASUVORK5CYII="

    def fake_openai(**kwargs):
        return _FakeOpenAIClient(
            [],
            payload={
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "image_url": {
                                        "url": f"data:image/png;base64,{one_pixel_png_b64}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_RESULT_FORMAT", "jpeg")
    monkeypatch.setattr("app.openrouter_client.OpenAI", fake_openai)

    result = openrouter_client.generate_image(
        model="openai/gpt-image-1",
        prompt="Draw this in oil painting",
        image_bytes=b"source-image",
    )

    assert result.startswith(b"\xff\xd8\xff")
    assert not result.startswith(b"\x89PNG")


def test_generate_image_resizes_large_input_before_request(monkeypatch) -> None:
    calls: list[dict] = []
    one_pixel_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2iR4sAAAAASUVORK5CYII="

    source = BytesIO()
    Image.new("RGB", (2800, 1900), color=(120, 160, 200)).save(source, format="JPEG", quality=95)
    large_input = source.getvalue()

    def fake_openai(**kwargs):
        return _FakeOpenAIClient(
            calls,
            payload={
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "image_url": {
                                        "url": f"data:image/png;base64,{one_pixel_png_b64}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_SOURCE_MAX_SIDE", "1280")
    monkeypatch.setattr("app.openrouter_client.OpenAI", fake_openai)

    openrouter_client.generate_image(
        model="openai/gpt-image-1",
        prompt="Resize before upstream call",
        image_bytes=large_input,
    )

    assert len(calls) == 1
    sent_data_url = calls[0]["messages"][0]["content"][1]["image_url"]["url"]
    sent_payload = base64.b64decode(sent_data_url.split(",", 1)[1])
    with Image.open(BytesIO(sent_payload)) as sent_image:
        assert max(sent_image.size) <= 1280


def test_generate_image_raises_if_response_has_no_images(monkeypatch) -> None:
    def fake_openai(**kwargs):
        return _FakeOpenAIClient([], payload={"choices": [{"message": {}}]})

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("app.openrouter_client.OpenAI", fake_openai)

    with pytest.raises(RuntimeError, match="OpenRouter response does not contain image data"):
        openrouter_client.generate_image(
            model="openai/gpt-image-1",
            prompt="Draw this in oil painting",
            image_bytes=b"source-image",
        )


def test_generate_image_includes_error_details_on_bad_request(monkeypatch) -> None:
    error = _FakeStatusError(
        404,
        {
            "error": {
                "message": "No endpoints found for openai/gpt-image-1."
            }
        },
    )

    def fake_openai(**kwargs):
        return _FakeOpenAIClient([], error=error)

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("app.openrouter_client.OpenAI", fake_openai)

    with pytest.raises(RuntimeError, match="No endpoints found for openai/gpt-image-1"):
        openrouter_client.generate_image(
            model="openai/gpt-image-1",
            prompt="Draw this in oil painting",
            image_bytes=b"source-image",
        )


def test_generate_image_reports_runtime_interpreter_when_openai_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("app.openrouter_client.OpenAI", None)

    def fail_import(name: str):
        raise ModuleNotFoundError("No module named 'openai'")

    monkeypatch.setattr("app.openrouter_client.importlib.import_module", fail_import)

    with pytest.raises(RuntimeError, match="runtime interpreter"):
        openrouter_client.generate_image(
            model="openai/gpt-image-1",
            prompt="Draw this in oil painting",
            image_bytes=b"source-image",
        )
