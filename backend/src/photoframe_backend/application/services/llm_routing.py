from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from urllib import error, request
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from photoframe_backend.infrastructure.clients import openai_compatible_client
from photoframe_backend.infrastructure.clients.openrouter_client import OPENROUTER_BASE_URL
from photoframe_backend.infrastructure.db.models import LlmRoutingSetting

STATUS_DISABLED = "disabled"
STATUS_TESTING = "testing"
STATUS_ACTIVE = "active"
STATUS_ERROR = "error"
DEFAULT_XRAY_CLIENT_URL = "http://xray-client:8081"
DEFAULT_LLM_EGRESS_URL = "http://llm-egress:8080"


def _now_utc_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def get_or_create_llm_routing_setting(db: Session) -> LlmRoutingSetting:
    setting = db.get(LlmRoutingSetting, 1)
    if setting is None:
        setting = LlmRoutingSetting(
            id=1,
            enabled=False,
            status=STATUS_DISABLED,
            vless_uri="",
            provider_base_url=OPENROUTER_BASE_URL,
            provider_api_key="",
            custom_providers_json="[]",
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def _post_json(url: str, payload: dict[str, object], timeout_seconds: float = 10.0) -> tuple[int, dict[str, object]]:
    encoded = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=encoded, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout_seconds) as response:
        body = response.read()
        parsed = json.loads(body.decode("utf-8")) if body else {}
        return response.getcode(), parsed


def _resolve_xray_client_url() -> str:
    return os.getenv("ROUTING_XRAY_CLIENT_URL", DEFAULT_XRAY_CLIENT_URL).rstrip("/")


def _resolve_llm_egress_url() -> str:
    return os.getenv("ROUTING_LLM_EGRESS_URL", DEFAULT_LLM_EGRESS_URL).rstrip("/")


def apply_vless_uri(vless_uri: str) -> tuple[bool, str | None]:
    if not vless_uri.strip():
        return False, "vless uri is empty"
    try:
        status_code, body = _post_json(f"{_resolve_xray_client_url()}/apply", {"vless_uri": vless_uri})
    except (OSError, error.URLError, ValueError) as exc:
        return False, str(exc)

    if status_code != 200:
        return False, str(body.get("detail") or f"xray apply failed ({status_code})")
    if body.get("ok") is True:
        return True, None
    return False, str(body.get("error") or "xray apply failed")


def _looks_like_openrouter(raw_base_url: str) -> bool:
    candidate = raw_base_url.strip().rstrip("/")
    if not candidate:
        return False
    parsed = urlparse(candidate)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() == "openrouter.ai"


def normalize_provider_base_url(raw_base_url: str | None) -> str:
    candidate = (raw_base_url or "").strip()
    if not candidate:
        return OPENROUTER_BASE_URL
    if _looks_like_openrouter(candidate):
        return OPENROUTER_BASE_URL
    return openai_compatible_client._normalize_base_url(candidate)


def normalize_custom_providers(raw_custom_providers: list[dict[str, str]] | list[object] | None) -> list[dict[str, str]]:
    if not raw_custom_providers:
        return []

    providers_by_url: dict[str, dict[str, str]] = {}
    for item in raw_custom_providers:
        if not isinstance(item, dict):
            continue
        base_url = normalize_provider_base_url(str(item.get("base_url") or ""))
        api_key = str(item.get("api_key") or "").strip()
        if not api_key:
            continue
        providers_by_url[base_url] = {"base_url": base_url, "api_key": api_key}
    return list(providers_by_url.values())


def resolve_selected_provider(setting: LlmRoutingSetting) -> tuple[str, str]:
    provider_base_url = normalize_provider_base_url(setting.provider_base_url)
    provider_api_key = setting.provider_api_key.strip()
    if provider_base_url == OPENROUTER_BASE_URL and not provider_api_key:
        for provider in setting.custom_providers:
            if provider["base_url"] == provider_base_url and provider["api_key"].strip():
                return provider_base_url, provider["api_key"].strip()
    return provider_base_url, provider_api_key


def probe_provider_base_url(provider_base_url: str) -> tuple[bool, str | None]:
    if not provider_base_url.strip():
        return False, "provider base url is empty"
    try:
        status_code, body = _post_json(f"{_resolve_llm_egress_url()}/probe", {"base_url": provider_base_url})
    except (OSError, error.URLError, ValueError) as exc:
        return False, str(exc)

    if status_code != 200:
        return False, str(body.get("detail") or f"probe failed ({status_code})")
    if body.get("ok") is True:
        return True, None
    return False, str(body.get("error") or "provider probe failed")


def _mark_success(setting: LlmRoutingSetting) -> None:
    now = _now_utc_naive()
    setting.last_error = None
    setting.last_checked_at = now
    setting.last_applied_at = now
    setting.status = STATUS_ACTIVE if setting.enabled else STATUS_DISABLED


def _mark_error(setting: LlmRoutingSetting, error: str) -> None:
    now = _now_utc_naive()
    setting.enabled = False
    setting.status = STATUS_ERROR
    setting.last_error = error
    setting.last_checked_at = now
    setting.last_applied_at = now


def _apply_and_probe(setting: LlmRoutingSetting) -> None:
    apply_ok, apply_error = apply_vless_uri(setting.vless_uri)
    if not apply_ok:
        _mark_error(setting, apply_error or "failed to apply vless uri")
        return

    provider_base_url, _ = resolve_selected_provider(setting)
    probe_ok, probe_error = probe_provider_base_url(provider_base_url)
    if probe_ok:
        _mark_success(setting)
        return

    _mark_error(setting, probe_error or "provider probe failed")


def save_vless_uri(
    db: Session, vless_uri: str
) -> LlmRoutingSetting:
    setting = get_or_create_llm_routing_setting(db)
    setting.vless_uri = vless_uri.strip()
    setting.status = STATUS_TESTING
    db.add(setting)
    db.commit()
    db.refresh(setting)

    _apply_and_probe(setting)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def save_provider_config(
    db: Session,
    *,
    provider_base_url: str,
    provider_api_key: str,
    custom_providers: list[dict[str, str]] | list[object] | None,
) -> LlmRoutingSetting:
    setting = get_or_create_llm_routing_setting(db)
    setting.provider_base_url = normalize_provider_base_url(provider_base_url)
    setting.provider_api_key = provider_api_key.strip()
    setting.custom_providers_json = json.dumps(normalize_custom_providers(custom_providers))
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def test_routing(db: Session) -> LlmRoutingSetting:
    setting = get_or_create_llm_routing_setting(db)
    if not setting.vless_uri.strip():
        _mark_error(setting, "vless uri is empty")
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting

    setting.status = STATUS_TESTING
    db.add(setting)
    db.commit()
    db.refresh(setting)

    _apply_and_probe(setting)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def set_routing_enabled(db: Session, enabled: bool) -> LlmRoutingSetting:
    setting = get_or_create_llm_routing_setting(db)
    if not enabled:
        setting.enabled = False
        setting.status = STATUS_DISABLED
        setting.last_error = None
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting

    setting.enabled = True
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return test_routing(db)


def is_llm_routing_active(db: Session) -> bool:
    setting = get_or_create_llm_routing_setting(db)
    return setting.enabled and setting.status == STATUS_ACTIVE


def get_routed_provider(db: Session) -> tuple[str, str]:
    setting = get_or_create_llm_routing_setting(db)
    return resolve_selected_provider(setting)
