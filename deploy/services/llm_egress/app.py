from __future__ import annotations

import base64
import logging
import os
from urllib.parse import urlsplit, urlunsplit

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

XRAY_HTTP_PROXY = os.getenv("XRAY_HTTP_PROXY", "http://xray-client:10809")
TIMEOUT_SECONDS = float(os.getenv("LLM_EGRESS_TIMEOUT_SECONDS", "30"))
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}
EXCLUDED_RESPONSE_HEADERS = HOP_BY_HOP_HEADERS | {"content-encoding"}

app = FastAPI(title="LLM Egress")
logger = logging.getLogger("llm_egress")


class ProbeRequest(BaseModel):
    base_url: str


def _format_error(exc: Exception) -> str:
    parts = [exc.__class__.__name__]
    details = str(exc).strip()
    if details:
        parts.append(details)

    cause = getattr(exc, "__cause__", None)
    if cause is not None:
        cause_text = str(cause).strip()
        parts.append(f"cause={cause.__class__.__name__}: {cause_text}" if cause_text else f"cause={cause.__class__.__name__}")

    context = getattr(exc, "__context__", None)
    if context is not None and context is not cause:
        context_text = str(context).strip()
        parts.append(
            f"context={context.__class__.__name__}: {context_text}" if context_text else f"context={context.__class__.__name__}"
        )

    return " | ".join(parts)


def _decode_base_url(encoded_base_url: str) -> str:
    padding = "=" * (-len(encoded_base_url) % 4)
    raw = base64.urlsafe_b64decode(f"{encoded_base_url}{padding}".encode("ascii"))
    return raw.decode("utf-8").rstrip("/")


def _forward_headers(headers: Request) -> dict[str, str]:
    return {key: value for key, value in headers.items() if key.lower() not in HOP_BY_HOP_HEADERS}


def _response_headers(headers: httpx.Headers) -> dict[str, str]:
    return {key: value for key, value in headers.items() if key.lower() not in EXCLUDED_RESPONSE_HEADERS}


def _build_target_url(base_url: str, path: str, query: str) -> str:
    normalized_path = f"/{path.lstrip('/')}" if path else ""
    combined = f"{base_url}{normalized_path}"
    parts = list(urlsplit(combined))
    parts[3] = query
    return urlunsplit(parts)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/probe")
async def probe(payload: ProbeRequest) -> JSONResponse:
    async with httpx.AsyncClient(proxy=XRAY_HTTP_PROXY, timeout=TIMEOUT_SECONDS, follow_redirects=False) as client:
        try:
            response = await client.head(payload.base_url)
            logger.info("probe HEAD %s -> %s", payload.base_url, response.status_code)
        except Exception:
            try:
                response = await client.get(payload.base_url)
                logger.info("probe GET %s -> %s", payload.base_url, response.status_code)
            except Exception as exc:
                formatted = _format_error(exc)
                logger.warning("probe failed for %s via %s: %s", payload.base_url, XRAY_HTTP_PROXY, formatted)
                return JSONResponse(status_code=200, content={"ok": False, "error": formatted})

    return JSONResponse(status_code=200, content={"ok": True, "status_code": response.status_code})


@app.api_route("/proxy/{encoded_base_url}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
@app.api_route(
    "/proxy/{encoded_base_url}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_request(encoded_base_url: str, request: Request, path: str = "") -> Response:
    upstream_base_url = _decode_base_url(encoded_base_url)
    target_url = _build_target_url(upstream_base_url, path, request.url.query)
    body = await request.body()

    async with httpx.AsyncClient(proxy=XRAY_HTTP_PROXY, timeout=TIMEOUT_SECONDS, follow_redirects=False) as client:
        upstream_response = await client.request(
            request.method,
            target_url,
            content=body,
            headers=_forward_headers(request.headers),
        )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=_response_headers(upstream_response.headers),
        media_type=upstream_response.headers.get("content-type"),
    )
