from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

XRAY_BIN = os.getenv("XRAY_BIN", "/usr/local/bin/xray")
XRAY_CONFIG_PATH = Path(os.getenv("XRAY_CONFIG_PATH", "/tmp/xray-config.json"))
XRAY_SOCKS_PORT = int(os.getenv("XRAY_SOCKS_PORT", "10808"))
XRAY_HTTP_PORT = int(os.getenv("XRAY_HTTP_PORT", "10809"))
XRAY_LOGLEVEL = os.getenv("XRAY_LOGLEVEL", "info")

app = FastAPI(title="Xray Client Control")
_lock = threading.Lock()
_process: subprocess.Popen[str] | None = None
logger = logging.getLogger("xray_client")


class ApplyRequest(BaseModel):
    vless_uri: str


def _first(query: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = query.get(key)
    if not values:
        return default
    return values[0]


def _parse_vless_uri(vless_uri: str) -> dict[str, object]:
    parsed = urlparse(vless_uri)
    if parsed.scheme != "vless":
        raise ValueError("unsupported uri scheme")
    if not parsed.username or not parsed.hostname or parsed.port is None:
        raise ValueError("vless uri must include user, host and port")

    query = parse_qs(parsed.query)
    security = (_first(query, "security") or "").lower()
    if security != "reality":
        raise ValueError("only VLESS Reality links are supported")

    server_name = _first(query, "sni")
    public_key = _first(query, "pbk")
    short_id = _first(query, "sid", "")
    fingerprint = _first(query, "fp", "chrome")
    network = _first(query, "type", "tcp")
    flow = _first(query, "flow")
    if not server_name or not public_key:
        raise ValueError("vless reality link is missing sni or pbk")
    if network != "tcp":
        raise ValueError("only tcp reality links are supported")

    return {
        "address": parsed.hostname,
        "port": parsed.port,
        "id": unquote(parsed.username),
        "server_name": server_name,
        "public_key": public_key,
        "short_id": short_id,
        "fingerprint": fingerprint,
        "flow": flow,
    }


def _build_config(vless_uri: str) -> dict[str, object]:
    parsed = _parse_vless_uri(vless_uri)
    user: dict[str, object] = {
        "id": parsed["id"],
        "encryption": "none",
    }
    if parsed["flow"]:
        user["flow"] = parsed["flow"]

    return {
        "log": {"loglevel": XRAY_LOGLEVEL},
        "inbounds": [
            {
                "tag": "socks-in",
                "listen": "0.0.0.0",
                "port": XRAY_SOCKS_PORT,
                "protocol": "socks",
                "settings": {"udp": True},
            },
            {
                "tag": "http-in",
                "listen": "0.0.0.0",
                "port": XRAY_HTTP_PORT,
                "protocol": "http",
                "settings": {},
            },
        ],
        "outbounds": [
            {
                "tag": "proxy",
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": parsed["address"],
                            "port": parsed["port"],
                            "users": [user],
                        }
                    ]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "serverName": parsed["server_name"],
                        "publicKey": parsed["public_key"],
                        "shortId": parsed["short_id"],
                        "fingerprint": parsed["fingerprint"],
                    },
                },
            },
            {"tag": "direct", "protocol": "freedom"},
        ],
    }


def _stop_process() -> None:
    global _process
    if _process is None:
        return
    _process.terminate()
    try:
        _process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _process.kill()
        _process.wait(timeout=5)
    _process = None


def _read_process_error() -> str:
    if _process is None or _process.stderr is None:
        return "xray process exited unexpectedly"
    stderr = _process.stderr.read().strip()
    return stderr or "xray process exited unexpectedly"


def _stream_lines(stream, prefix: str) -> None:
    if stream is None:
        return

    for raw_line in stream:
        line = raw_line.strip()
        if line:
            logger.warning("%s: %s", prefix, line)


def _wait_until_proxy_ready(timeout_seconds: float = 5.0) -> tuple[bool, str | None]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _process is None:
            return False, "xray process is not running"
        if _process.poll() is not None:
            return False, _read_process_error()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            try:
                sock.connect(("127.0.0.1", XRAY_HTTP_PORT))
                return True, None
            except OSError:
                time.sleep(0.1)

    return False, f"xray proxy on port {XRAY_HTTP_PORT} did not become ready in time"


def _start_process() -> tuple[bool, str | None]:
    global _process
    try:
        _process = subprocess.Popen(
            [XRAY_BIN, "run", "-c", str(XRAY_CONFIG_PATH)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        _process = None
        return False, str(exc)

    threading.Thread(target=_stream_lines, args=(_process.stdout, "xray-stdout"), daemon=True).start()
    threading.Thread(target=_stream_lines, args=(_process.stderr, "xray-stderr"), daemon=True).start()
    return _wait_until_proxy_ready()


@app.on_event("shutdown")
def shutdown() -> None:
    with _lock:
        _stop_process()


@app.get("/health")
async def health() -> dict[str, object]:
    with _lock:
        running = _process is not None and _process.poll() is None
    return {"status": "ok" if running else "idle"}


@app.post("/apply")
async def apply(payload: ApplyRequest) -> JSONResponse:
    try:
        config = _build_config(payload.vless_uri)
    except ValueError as exc:
        logger.warning("xray apply rejected invalid vless uri: %s", exc)
        return JSONResponse(status_code=200, content={"ok": False, "error": str(exc)})

    XRAY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    XRAY_CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=True), encoding="utf-8")

    with _lock:
        test_run = subprocess.run(
            [XRAY_BIN, "run", "-test", "-c", str(XRAY_CONFIG_PATH)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if test_run.returncode != 0:
            error_text = (test_run.stderr or test_run.stdout or "xray config test failed").strip()
            logger.warning("xray config test failed: %s", error_text)
            return JSONResponse(status_code=200, content={"ok": False, "error": error_text})

        _stop_process()
        started, start_error = _start_process()
        if not started:
            logger.warning("xray process failed to start cleanly: %s", start_error)
            return JSONResponse(status_code=200, content={"ok": False, "error": start_error or "failed to start xray"})

    logger.info("xray config applied successfully")
    return JSONResponse(status_code=200, content={"ok": True})
