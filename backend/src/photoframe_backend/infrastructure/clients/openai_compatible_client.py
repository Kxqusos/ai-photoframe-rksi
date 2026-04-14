import base64
import os
from io import BytesIO
from urllib.parse import urlparse

from photoframe_backend.infrastructure.clients.openrouter_client import (
    _extract_image_b64_from_legacy_data,
    _load_openai_client_class,
    _prepare_source_image_for_request,
    _response_to_dict,
    _transform_output_image,
)


def _normalize_base_url(raw_base_url: str | None) -> str:
    candidate = (raw_base_url or "").strip().rstrip("/")
    if not candidate:
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL is not configured")

    parsed = urlparse(candidate)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL must be an absolute URL")

    if parsed.path in {"", "/"}:
        return f"{candidate}/v1"
    return candidate


def generate_image(*, model: str, prompt: str, image_bytes: bytes, base_url: str | None = None, api_key: str | None = None) -> bytes:
    resolved_api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY")
    if not resolved_api_key:
        raise RuntimeError("OPENAI_COMPATIBLE_API_KEY is not configured")

    openai_client_class = _load_openai_client_class()
    client = openai_client_class(
        api_key=resolved_api_key,
        base_url=base_url or _normalize_base_url(os.getenv("OPENAI_COMPATIBLE_BASE_URL")),
        timeout=120.0,
    )

    prepared_source = _prepare_source_image_for_request(image_bytes)
    upload = BytesIO(prepared_source)
    upload.name = "source.jpg"

    response = client.images.edit(
        model=model,
        image=upload,
        prompt=prompt,
    )

    data = _response_to_dict(response)
    encoded_image = _extract_image_b64_from_legacy_data(data)
    if not encoded_image:
        raise RuntimeError("API response does not contain image data")

    return _transform_output_image(base64.b64decode(encoded_image))


__all__ = ["generate_image"]
