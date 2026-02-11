import base64
import os
from typing import Any

import httpx

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


def _extract_image_data_url_from_choices(payload: dict[str, Any]) -> str | None:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return None

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return None

    images = message.get("images")
    if not isinstance(images, list) or not images:
        return None

    first_image = images[0]
    if not isinstance(first_image, dict):
        return None

    image_url = first_image.get("image_url")
    if isinstance(image_url, dict):
        value = image_url.get("url")
        if isinstance(value, str):
            return value

    image_url_camel = first_image.get("imageUrl")
    if isinstance(image_url_camel, dict):
        value = image_url_camel.get("url")
        if isinstance(value, str):
            return value

    return None


def _extract_image_b64_from_legacy_data(payload: dict[str, Any]) -> str | None:
    data = payload.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            b64_value = first.get("b64_json")
            if isinstance(b64_value, str):
                return b64_value
    return None


def _decode_image_data(data_url_or_b64: str) -> bytes:
    value = data_url_or_b64.strip()
    if value.startswith("data:image/"):
        parts = value.split(",", 1)
        if len(parts) != 2:
            raise RuntimeError("OpenRouter image data URL is invalid")
        return base64.b64decode(parts[1])
    return base64.b64decode(value)


def generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
                ],
            }
        ],
        "modalities": ["image", "text"],
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    http_referer = os.getenv("OPENROUTER_HTTP_REFERER")
    if http_referer:
        headers["HTTP-Referer"] = http_referer
    x_title = os.getenv("OPENROUTER_X_TITLE")
    if x_title:
        headers["X-Title"] = x_title

    with httpx.Client(timeout=120.0) as client:
        response = client.post(OPENROUTER_CHAT_COMPLETIONS_URL, json=payload, headers=headers)
        response.raise_for_status()

    data = response.json()
    data_url_or_b64 = _extract_image_data_url_from_choices(data)
    if not data_url_or_b64:
        data_url_or_b64 = _extract_image_b64_from_legacy_data(data)
    if not data_url_or_b64:
        raise RuntimeError("OpenRouter response does not contain image data")
    return _decode_image_data(data_url_or_b64)
