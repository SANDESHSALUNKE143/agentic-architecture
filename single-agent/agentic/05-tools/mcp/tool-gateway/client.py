"""MCP client.

Purpose: open one session with a configured MCP server and call a tool. This file holds no merchant records.
Used by: the catalog, order, billing, and support tool modules, and by the connection check.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import uuid
from urllib.parse import urlsplit, urlunsplit

import httpx
from agentic.platform.config import setting
from guardrails.connections.mcp_servers import any_credentials, credentials

logger = logging.getLogger("agentic.mcp")

PROTOCOL = "2024-11-05"
MAX_BODY = 32_000
MAX_RESPONSE = 256_000
WRITES = {"prepare_order", "request_approval"}
_LOCK = threading.Lock()
_SESSIONS: dict[str, str] = {}
_HTTP = httpx.Client(
    follow_redirects=False,
    trust_env=True,
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
)


class _SessionExpired(Exception):
    pass


class _Rejected(Exception):
    pass


def call_tool(purpose: str, name: str, arguments: dict) -> dict:
    located = credentials(purpose)
    if located is None:
        return {"error": "connection_required", "explanation": f"No MCP server is configured for {purpose}."}
    if not isinstance(arguments, dict):
        return {"error": "upstream_rejected", "explanation": "Tool arguments must be an object."}
    url, token = located
    return _attempt(url, token, "tools/call", {"name": name, "arguments": arguments}, retry=name not in WRITES)


def list_tools() -> dict:
    located = any_credentials()
    if located is None:
        return {"tools": [], "explanation": "No MCP server is configured.", "error": "connection_required"}
    url, token = located
    result = _attempt(url, token, "tools/list", {}, retry=True)
    if result.get("error"):
        return {"tools": [], "explanation": result["explanation"], "error": result["error"]}
    names = []
    for item in result.get("tools") or []:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"])[:80])
    return {"tools": names, "explanation": "The MCP server listed its tools.", "submitted": False}


def ping(url: str, token: str) -> tuple[str, str]:
    outcome = _attempt(url, token, "initialize", _initialize_params(), retry=False, raw=True)
    if outcome.get("error"):
        return "failed", "The server did not answer the MCP initialize call."
    return "ok", "The server accepted the MCP initialize call."


def _attempt(url: str, token: str, method: str, params: dict, retry: bool, raw: bool = False) -> dict:
    tries = 2 if retry else 1
    for attempt in range(tries):
        try:
            if method == "initialize":
                _open(url, token)
                return {"ok": True}
            session = _session(url, token)
            result = _rpc(url, token, method, params, session)
            return result if raw else _unwrap(result)
        except _SessionExpired:
            _drop(url, token)
            if attempt + 1 < tries:
                continue
        except _Rejected as exc:
            return {"error": "upstream_rejected", "explanation": str(exc)[:300]}
        except (httpx.HTTPError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
            logger.warning("MCP call to %s failed", _host(url))
            if attempt + 1 < tries:
                continue
    return {"error": "upstream_unavailable", "explanation": "The MCP server did not answer."}


def _session(url: str, token: str) -> str:
    key = _key(url, token)
    with _LOCK:
        found = _SESSIONS.get(key, "")
    if found:
        return found
    session = _open(url, token)
    with _LOCK:
        _SESSIONS[key] = session
    return session


def _open(url: str, token: str) -> str:
    session, body = _post(url, token, "initialize", _initialize_params(), "")
    _raise_for_body(body)
    if session:
        try:
            _post(url, token, "notifications/initialized", {}, session)
        except _Rejected:
            raise
        except (httpx.HTTPError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
            logger.warning("MCP server %s accepted initialize and skipped the initialized notification", _host(url))
    return session


def _rpc(url: str, token: str, method: str, params: dict, session: str) -> dict:
    _session_id, body = _post(url, token, method, params, session)
    _raise_for_body(body)
    result = body.get("result")
    if not isinstance(result, dict):
        raise ValueError("The MCP server returned no result.")
    return result


def _post(url: str, token: str, method: str, params: dict, session: str) -> tuple[str, dict]:
    request_id = None if method.startswith("notifications/") else uuid.uuid4().hex
    payload = {"jsonrpc": "2.0", "method": method, "params": params}
    if request_id is not None:
        payload["id"] = request_id
    raw = json.dumps(payload).encode()
    if len(raw) > MAX_BODY:
        raise _Rejected("The tool arguments are too large.")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOL,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if session:
        headers["Mcp-Session-Id"] = session
    timeout = httpx.Timeout(float(setting("MCP_HTTP_TIMEOUT", "5") or "5"), connect=2.0)
    with _HTTP.stream("POST", url, content=raw, headers=headers, timeout=timeout) as response:
        if response.status_code in {301, 302, 303, 307, 308}:
            raise _Rejected("The MCP server returned a redirect. The client does not follow it.")
        if response.status_code in {401, 403}:
            raise _Rejected("The MCP server refused the token.")
        if response.status_code == 404 and session:
            raise _SessionExpired()
        if response.status_code >= 400:
            raise ValueError(f"HTTP {response.status_code}")
        issued = response.headers.get("mcp-session-id", "").strip()[:200]
        content_type = response.headers.get("content-type", "")
        collected = bytearray()
        for chunk in response.iter_bytes():
            collected.extend(chunk)
            if len(collected) > MAX_RESPONSE:
                raise ValueError("response too large")
    return issued, _decode(content_type, bytes(collected), request_id)


def _decode(content_type: str, raw: bytes, request_id: str | None) -> dict:
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return {}
    if "text/event-stream" in content_type:
        messages = []
        for line in text.splitlines():
            if not line.startswith("data:"):
                continue
            piece = line[5:].strip()
            if piece and piece != "[DONE]":
                parsed = json.loads(piece)
                if isinstance(parsed, dict):
                    messages.append(parsed)
        if not messages:
            raise ValueError("The MCP server returned an empty stream.")
        matched = [item for item in messages if request_id is None or item.get("id") in {None, request_id}]
        return matched[-1] if matched else messages[-1]
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("The MCP server returned an unexpected body.")
    return parsed


def _raise_for_body(body: dict) -> None:
    error = body.get("error")
    if not isinstance(error, dict):
        return
    code = error.get("code")
    if code in {-32000, -32001}:
        raise _SessionExpired()
    message = str(error.get("message") or "The MCP server rejected the call.")
    raise _Rejected(message.replace("Bearer ", "")[:300])


def _unwrap(result: dict) -> dict:
    if result.get("isError"):
        text = _text(result) or "The MCP server rejected the call."
        return {"error": "upstream_rejected", "explanation": text[:300]}
    text = _text(result)
    if not text:
        return result
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"explanation": text[:300]}
    return parsed if isinstance(parsed, dict) else {"explanation": text[:300]}


def _text(result: dict) -> str:
    content = result.get("content")
    if not isinstance(content, list) or not content or not isinstance(content[0], dict):
        return ""
    return str(content[0].get("text") or "")


def _initialize_params() -> dict:
    return {
        "protocolVersion": PROTOCOL,
        "capabilities": {},
        "clientInfo": {"name": "agentic-architecture", "version": "1.0.0"},
    }


def _drop(url: str, token: str) -> None:
    with _LOCK:
        _SESSIONS.pop(_key(url, token), None)


def _key(url: str, token: str) -> str:
    digest = hashlib.sha256(token.encode()).hexdigest()[:16]
    return f"{url}|{digest}"


def _host(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
