"""MCP servers this process can be pointed at.

Purpose: store more than one MCP server address. Each server has a purpose, a URL, and a token. The token is not returned.
Used by: the Plugins page, the MCP client, and the gateway readiness check. The initialize call is mcp_probe.py.
"""

from __future__ import annotations

import json
import os
import re
from urllib.parse import urlparse

from shared.config import data_dir

PURPOSES = ("product", "orders", "billing", "support", "research", "other")
MERCHANT_PURPOSES = ("product", "orders", "billing", "support")


def _path():
    return data_dir() / "mcp-servers.json"


def _read() -> dict:
    path = _path()
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _write(payload: dict) -> None:
    _path().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _slug(title: str, taken: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "mcp-server"
    candidate = base
    number = 2
    while candidate in taken:
        candidate = f"{base}-{number}"
        number += 1
    return candidate


def _purpose(value: str) -> str:
    choice = (value or "other").strip().lower()
    if choice not in PURPOSES:
        raise ValueError("Purpose must be product, orders, billing, support, research, or other.")
    return choice


def _url(value: str) -> str:
    url = value.strip()[:500]
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("The MCP server URL must start with http:// or https://.")
    if parsed.username or parsed.password:
        raise ValueError("Put the token in the token field. The URL must not contain credentials.")
    return url


def _configured_url(value: str) -> str:
    try:
        return _url(value)
    except ValueError:
        return ""


def credentials(purpose: str) -> tuple[str, str] | None:
    for item in _read().values():
        if not isinstance(item, dict) or str(item.get("purpose") or "") != purpose:
            continue
        url = _configured_url(str(item.get("url") or ""))
        if url:
            return url, str(item.get("password") or "").strip()
    if purpose in MERCHANT_PURPOSES:
        url = _configured_url(os.environ.get("MERCHANT_MCP_URL", ""))
        if url:
            return url, os.environ.get("MERCHANT_MCP_TOKEN", "").strip()
    return None


def saved_for(purpose: str) -> dict | None:
    for server_id, item in _read().items():
        if not isinstance(item, dict) or str(item.get("purpose") or "") != purpose:
            continue
        if _configured_url(str(item.get("url") or "")):
            return next(row for row in public() if row["id"] == server_id)
    return None


def purpose_ready(purpose: str) -> bool:
    return credentials(purpose) is not None


def address(purpose: str) -> str:
    located = credentials(purpose)
    return located[0] if located else ""


def any_credentials() -> tuple[str, str] | None:
    for item in _read().values():
        if not isinstance(item, dict):
            continue
        url = _configured_url(str(item.get("url") or ""))
        if url:
            return url, str(item.get("password") or "").strip()
    for url_name, token_name in (("MCP_SERVER_URL", "MCP_SERVER_TOKEN"), ("MERCHANT_MCP_URL", "MERCHANT_MCP_TOKEN")):
        url = _configured_url(os.environ.get(url_name, ""))
        if url:
            return url, os.environ.get(token_name, "").strip()
    return None


def any_configured() -> bool:
    if os.environ.get("MCP_SERVER_URL", "").strip():
        return True
    return any(str(item.get("url") or "").strip() for item in _read().values() if isinstance(item, dict))


def public() -> list[dict]:
    rows = []
    for server_id, item in _read().items():
        if not isinstance(item, dict):
            continue
        rows.append({
            "id": server_id,
            "title": str(item.get("title") or server_id),
            "purpose": str(item.get("purpose") or "other"),
            "url": str(item.get("url") or ""),
            "username": str(item.get("username") or ""),
            "password_set": bool(str(item.get("password") or "").strip()),
            "configured": bool(str(item.get("url") or "").strip()),
            "check_status": str(item.get("check_status") or ""),
            "check_detail": str(item.get("check_detail") or ""),
        })
    return sorted(rows, key=lambda row: row["title"].lower())


def add(title: str, purpose: str, url: str, username: str, password: str) -> dict:
    name = title.strip()[:80]
    if not name:
        raise ValueError("Name the MCP server.")
    current = _read()
    if len(current) >= 24:
        raise ValueError("Twenty-four MCP servers is the limit.")
    server_id = _slug(name, set(current))
    current[server_id] = {
        "title": name,
        "purpose": _purpose(purpose),
        "url": _url(url),
        "username": username.strip()[:200],
        "password": password.strip()[:200],
        "check_status": "",
        "check_detail": "",
    }
    _write(current)
    return next(row for row in public() if row["id"] == server_id)


def update(server_id: str, title: str, purpose: str, url: str, username: str, password: str) -> dict:
    current = _read()
    previous = current.get(server_id)
    if not isinstance(previous, dict):
        raise ValueError("Unknown MCP server.")
    name = title.strip()[:80] or str(previous.get("title") or server_id)
    incoming_password = password.strip()
    current[server_id] = {
        "title": name,
        "purpose": _purpose(purpose),
        "url": _url(url),
        "username": username.strip()[:200],
        "password": incoming_password[:200] if incoming_password else str(previous.get("password") or ""),
        "check_status": "",
        "check_detail": "",
    }
    _write(current)
    return next(row for row in public() if row["id"] == server_id)


def remove(server_id: str) -> None:
    current = _read()
    if server_id not in current:
        raise ValueError("Unknown MCP server.")
    del current[server_id]
    _write(current)


def record_check(server_id: str, status: str, detail: str) -> dict:
    current = _read()
    item = current.get(server_id)
    if not isinstance(item, dict):
        raise ValueError("Unknown MCP server.")
    item["check_status"] = status
    item["check_detail"] = detail[:300]
    current[server_id] = item
    _write(current)
    return next(row for row in public() if row["id"] == server_id)
