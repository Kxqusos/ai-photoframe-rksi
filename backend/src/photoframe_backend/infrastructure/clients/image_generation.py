import base64
import os
from photoframe_backend.infrastructure.clients import openai_compatible_client, openrouter_client
from photoframe_backend.infrastructure.clients.openrouter_client import OPENROUTER_BASE_URL

DEFAULT_LLM_EGRESS_URL = "http://llm-egress:8080"


def _resolve_llm_egress_url() -> str:
    return os.getenv("ROUTING_LLM_EGRESS_URL", DEFAULT_LLM_EGRESS_URL).rstrip("/")


def _build_routed_base_url(upstream_base_url: str) -> str:
    encoded = base64.urlsafe_b64encode(upstream_base_url.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{_resolve_llm_egress_url()}/proxy/{encoded}"


def _normalize_selected_provider_base_url(raw_base_url: str) -> str:
    candidate = raw_base_url.strip()
    if not candidate:
        return OPENROUTER_BASE_URL
    if "openrouter.ai" in candidate:
        return OPENROUTER_BASE_URL
    return openai_compatible_client._normalize_base_url(candidate)


def generate_image(
    *,
    model: str,
    prompt: str,
    image_bytes: bytes,
    route_via_proxy: bool = False,
    provider_base_url: str | None = None,
    provider_api_key: str | None = None,
) -> bytes:
    upstream_base_url = _normalize_selected_provider_base_url(provider_base_url or "")
    if route_via_proxy:
        base_url = _build_routed_base_url(upstream_base_url)
        if upstream_base_url == OPENROUTER_BASE_URL:
            return openrouter_client.generate_image(
                model=model,
                prompt=prompt,
                image_bytes=image_bytes,
                base_url=base_url,
                api_key=provider_api_key,
            )
        return openai_compatible_client.generate_image(
            model=model,
            prompt=prompt,
            image_bytes=image_bytes,
            base_url=base_url,
            api_key=provider_api_key,
        )
    if upstream_base_url == OPENROUTER_BASE_URL:
        return openrouter_client.generate_image(
            model=model,
            prompt=prompt,
            image_bytes=image_bytes,
            base_url=upstream_base_url,
            api_key=provider_api_key,
        )
    return openai_compatible_client.generate_image(
        model=model,
        prompt=prompt,
        image_bytes=image_bytes,
        base_url=upstream_base_url,
        api_key=provider_api_key,
    )


__all__ = ["generate_image"]
