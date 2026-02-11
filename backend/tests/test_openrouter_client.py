import base64
from typing import Any

import pytest

from app import openrouter_client


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeClient:
    def __init__(self, *, payload: dict[str, Any], calls: list[dict[str, Any]]) -> None:
        self._payload = payload
        self._calls = calls

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, *, json: dict[str, Any], headers: dict[str, str]):
        self._calls.append({"url": url, "json": json, "headers": headers})
        return _FakeResponse(self._payload)


def test_generate_image_uses_chat_completions_payload(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    encoded = base64.b64encode(b"generated-image").decode("utf-8")

    def fake_client(*args, **kwargs):
        return _FakeClient(
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
            calls=calls,
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_HTTP_REFERER", "https://photoframe.local")
    monkeypatch.setenv("OPENROUTER_X_TITLE", "AI Photoframe")
    monkeypatch.setattr("app.openrouter_client.httpx.Client", fake_client)

    result = openrouter_client.generate_image(
        model="google/gemini-2.5-flash-image-preview",
        prompt="Draw this in watercolor style",
        image_bytes=b"source-image",
    )

    assert result == b"generated-image"
    assert len(calls) == 1

    call = calls[0]
    assert call["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert call["json"]["modalities"] == ["image", "text"]
    assert call["json"]["messages"][0]["role"] == "user"
    content = call["json"]["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "Draw this in watercolor style"
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    headers = call["headers"]
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["HTTP-Referer"] == "https://photoframe.local"
    assert headers["X-Title"] == "AI Photoframe"


def test_generate_image_supports_camel_case_image_url(monkeypatch) -> None:
    encoded = base64.b64encode(b"generated-camel").decode("utf-8")

    def fake_client(*args, **kwargs):
        return _FakeClient(
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
            calls=[],
        )

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("app.openrouter_client.httpx.Client", fake_client)

    result = openrouter_client.generate_image(
        model="google/gemini-2.5-flash-image-preview",
        prompt="Draw this in oil painting",
        image_bytes=b"source-image",
    )

    assert result == b"generated-camel"


def test_generate_image_raises_if_response_has_no_images(monkeypatch) -> None:
    def fake_client(*args, **kwargs):
        return _FakeClient(payload={"choices": [{"message": {}}]}, calls=[])

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("app.openrouter_client.httpx.Client", fake_client)

    with pytest.raises(RuntimeError, match="OpenRouter response does not contain image data"):
        openrouter_client.generate_image(
            model="google/gemini-2.5-flash-image-preview",
            prompt="Draw this in oil painting",
            image_bytes=b"source-image",
        )
