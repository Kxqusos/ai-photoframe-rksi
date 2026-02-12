import base64
import importlib
import logging
import os
import sys
import time
from io import BytesIO
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError

OpenAI = None

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_PROVIDER_SORT = "throughput"
DEFAULT_PREFERRED_MAX_LATENCY_SECONDS = 25
DEFAULT_RESULT_FORMAT = "jpeg"
DEFAULT_JPEG_QUALITY = 85
DEFAULT_SOURCE_MAX_SIDE = 1280
DEFAULT_SOURCE_JPEG_QUALITY = 85
logger = logging.getLogger(__name__)


def _load_openai_client_class():
    global OpenAI

    if OpenAI is not None:
        return OpenAI

    try:
        module = importlib.import_module("openai")
        openai_cls = getattr(module, "OpenAI")
    except Exception as exc:
        details = str(exc).strip()
        suffix = f": {details}" if details else ""
        raise RuntimeError(
            "openai package is not installed in runtime interpreter "
            f"({sys.executable}). Run backend with `cd backend && uv run uvicorn app.main:app --reload`{suffix}"
        ) from exc

    OpenAI = openai_cls
    return openai_cls


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


def _extract_error_message(payload: dict[str, Any]) -> str | None:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    if isinstance(error, str) and error.strip():
        return error.strip()
    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None


def _response_to_dict(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response

    model_dump = getattr(response, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, dict):
            return dumped

    to_dict = getattr(response, "to_dict", None)
    if callable(to_dict):
        dumped = to_dict()
        if isinstance(dumped, dict):
            return dumped

    raise RuntimeError("OpenRouter response has unsupported format")


def _format_openrouter_error(exc: Exception) -> RuntimeError:
    status_code = getattr(exc, "status_code", None)

    payload: dict[str, Any] | None = None
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        payload = body

    if payload is None:
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                maybe_payload = response.json()
                if isinstance(maybe_payload, dict):
                    payload = maybe_payload
            except Exception:
                payload = None

    details = _extract_error_message(payload) if payload else None
    if not details:
        text = str(exc).strip()
        details = text or None

    status = status_code if isinstance(status_code, int) else 500
    suffix = f": {details}" if details else ""
    return RuntimeError(f"OpenRouter request failed ({status}){suffix}")


def _parse_positive_int(value: str | None) -> int | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    try:
        parsed = int(candidate)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _build_extra_body() -> dict[str, Any]:
    provider: dict[str, Any] = {}
    provider_sort = os.getenv("OPENROUTER_PROVIDER_SORT", DEFAULT_PROVIDER_SORT).strip()
    if provider_sort:
        provider["sort"] = provider_sort

    preferred_max_latency = _parse_positive_int(
        os.getenv("OPENROUTER_PREFERRED_MAX_LATENCY", str(DEFAULT_PREFERRED_MAX_LATENCY_SECONDS))
    )
    if preferred_max_latency is not None:
        provider["preferred_max_latency"] = preferred_max_latency

    extra_body: dict[str, Any] = {"modalities": ["image", "text"], "stream": False}
    if provider:
        extra_body["provider"] = provider
    return extra_body


def _resolve_result_format() -> str:
    raw_format = os.getenv("OPENROUTER_RESULT_FORMAT", DEFAULT_RESULT_FORMAT).strip().lower()
    if raw_format in {"jpg", "jpeg"}:
        return "jpeg"
    if raw_format == "png":
        return "png"
    return DEFAULT_RESULT_FORMAT


def _resolve_jpeg_quality() -> int:
    parsed = _parse_positive_int(os.getenv("OPENROUTER_JPEG_QUALITY", str(DEFAULT_JPEG_QUALITY)))
    if parsed is None:
        return DEFAULT_JPEG_QUALITY
    return max(1, min(parsed, 95))


def _resolve_source_max_side() -> int | None:
    parsed = _parse_positive_int(os.getenv("OPENROUTER_SOURCE_MAX_SIDE", str(DEFAULT_SOURCE_MAX_SIDE)))
    return parsed if parsed is not None else DEFAULT_SOURCE_MAX_SIDE


def _resolve_source_jpeg_quality() -> int:
    parsed = _parse_positive_int(os.getenv("OPENROUTER_SOURCE_JPEG_QUALITY", str(DEFAULT_SOURCE_JPEG_QUALITY)))
    if parsed is None:
        return DEFAULT_SOURCE_JPEG_QUALITY
    return max(1, min(parsed, 95))


def _prepare_source_image_for_request(image_bytes: bytes) -> bytes:
    max_side = _resolve_source_max_side()
    if max_side is None:
        return image_bytes

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            original_size = image.size
            normalized = ImageOps.exif_transpose(image)

            longest_side = max(normalized.size)
            needs_resize = longest_side > max_side
            if needs_resize:
                scale = max_side / float(longest_side)
                target_size = (
                    max(1, int(round(normalized.size[0] * scale))),
                    max(1, int(round(normalized.size[1] * scale))),
                )
                normalized = normalized.resize(target_size, Image.Resampling.LANCZOS)

            if not needs_resize and image_bytes.startswith(b"\xff\xd8\xff"):
                return image_bytes

            converted = normalized.convert("RGB")
            output = BytesIO()
            converted.save(
                output,
                format="JPEG",
                quality=_resolve_source_jpeg_quality(),
                optimize=True,
            )
            prepared = output.getvalue()
            logger.info(
                "Prepared source image for OpenRouter: %sx%s -> %sx%s, %d -> %d bytes",
                original_size[0],
                original_size[1],
                converted.size[0],
                converted.size[1],
                len(image_bytes),
                len(prepared),
            )
            return prepared
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        logger.warning("Failed to preprocess source image (%s); sending original bytes", exc.__class__.__name__)
        return image_bytes


def _convert_image_to_jpeg(image_bytes: bytes) -> bytes:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return image_bytes

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            converted = image.convert("RGB")
            output = BytesIO()
            converted.save(output, format="JPEG", quality=_resolve_jpeg_quality(), optimize=True)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        logger.warning("Failed to convert generated image to JPEG (%s); storing original bytes", exc.__class__.__name__)
        return image_bytes


def _transform_output_image(image_bytes: bytes) -> bytes:
    target_format = _resolve_result_format()
    if target_format == "jpeg":
        return _convert_image_to_jpeg(image_bytes)
    return image_bytes


def generate_image(*, model: str, prompt: str, image_bytes: bytes) -> bytes:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    openai_client_class = _load_openai_client_class()

    headers: dict[str, str] = {}
    http_referer = os.getenv("OPENROUTER_HTTP_REFERER")
    if http_referer:
        headers["HTTP-Referer"] = http_referer
    x_title = os.getenv("OPENROUTER_X_TITLE")
    if x_title:
        headers["X-Title"] = x_title

    client = openai_client_class(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers=headers,
        timeout=120.0,
    )

    prepared_source = _prepare_source_image_for_request(image_bytes)
    encoded_image = base64.b64encode(prepared_source).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
            ],
        }
    ]

    request_started = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            extra_body=_build_extra_body(),
        )
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - request_started) * 1000)
        logger.warning(
            "OpenRouter request failed in %sms (model=%s, input_bytes=%d)",
            elapsed_ms,
            model,
            len(prepared_source),
        )
        raise _format_openrouter_error(exc) from exc

    data = _response_to_dict(response)
    elapsed_ms = int((time.perf_counter() - request_started) * 1000)
    logger.info(
        "OpenRouter request completed in %sms (model=%s, input_bytes=%d)",
        elapsed_ms,
        model,
        len(prepared_source),
    )
    data_url_or_b64 = _extract_image_data_url_from_choices(data)
    if not data_url_or_b64:
        data_url_or_b64 = _extract_image_b64_from_legacy_data(data)
    if not data_url_or_b64:
        raise RuntimeError("OpenRouter response does not contain image data")
    decoded = _decode_image_data(data_url_or_b64)
    return _transform_output_image(decoded)
