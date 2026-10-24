"""Example merchant MCP server.

Purpose: a separate process that owns products, orders, discounts, and support drafts. The agent platform is the client.
Used by: start-local.sh and tests. Replace records.json with a real merchant system; this process is the third party.
"""

from __future__ import annotations

import inspect
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RECORDS = Path(__file__).with_name("records.json")
MAX_BODY = 65_536
MAX_RECORDS = 500
DRAFTS: list[dict] = []
REQUESTS: list[dict] = []
SESSIONS: set[str] = set()
_STATE = threading.Lock()


def load_records() -> dict:
    loaded = json.loads(RECORDS.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _products() -> list[dict]:
    rows = load_records().get("products") or []
    return [row for row in rows if isinstance(row, dict)]


def _orders() -> list[dict]:
    rows = load_records().get("orders") or []
    return [row for row in rows if isinstance(row, dict)]


def _discounts() -> list[dict]:
    rows = load_records().get("discounts") or []
    return [row for row in rows if isinstance(row, dict)]


def search_products(query: str = "") -> dict:
    tokens = [token for token in str(query)[:500].lower().split() if len(token) > 2]
    found = []
    for product in _products():
        haystack = f"{product.get('name', '')} {product.get('product_id', '')}".lower()
        if any(token in haystack for token in tokens):
            found.append(product)
    return {
        "products": found,
        "sources": [{"source_id": item.get("source_id", ""), "location": "merchant-mcp"} for item in found],
        "explanation": f"Found {len(found)} product(s) on the merchant MCP server.",
    }


def get_product_details(product_id: str = "") -> dict:
    product = next((item for item in _products() if item.get("product_id") == product_id), None)
    if not product:
        return {"products": [], "explanation": "The merchant MCP server has no matching product.", "sources": []}
    return {
        "products": [product],
        "explanation": f"{product.get('name', 'Product')} costs {product.get('price')}.",
        "sources": [{"source_id": product.get("source_id", ""), "location": "merchant-mcp"}],
    }


def compare_products(product_ids: list | None = None) -> dict:
    wanted = product_ids if isinstance(product_ids, list) else []
    items = [item for item in _products() if item.get("product_id") in wanted]
    return {
        "products": items,
        "explanation": "The merchant MCP server compared the listed products by price.",
        "sources": [{"source_id": item.get("source_id", ""), "location": "merchant-mcp"} for item in items],
    }


def check_stock(product_id: str = "") -> dict:
    product = next((item for item in _products() if item.get("product_id") == product_id), None)
    if not product:
        return {
            "product_id": product_id,
            "available": 0,
            "explanation": "The merchant MCP server has no matching product.",
            "sources": [],
        }
    stock = product.get("stock", 0)
    return {
        "product_id": product.get("product_id", product_id),
        "available": stock,
        "explanation": f"{product.get('name', 'Product')} has {stock} in stock.",
        "sources": [{"source_id": product.get("source_id", ""), "location": "merchant-mcp"}],
    }


def get_order_status(order_id: str = "") -> dict:
    key = str(order_id)
    order = next((item for item in _orders() if str(item.get("order_id")) == key), None)
    if not order:
        order = {"order_id": key, "status": "unknown", "product_id": ""}
    return {
        "order_id": order.get("order_id", key),
        "status": order.get("status", "unknown"),
        "explanation": f"Order {order.get('order_id', key)} is {order.get('status', 'unknown')} on the merchant MCP server.",
    }


def prepare_order(product_id: str = "", user_id: str = "", amount: float = 0, approved: bool = False) -> dict:
    draft = {
        "product_id": product_id,
        "user_id": user_id,
        "amount": amount,
        "approved": approved,
        "submitted": False,
    }
    _remember(DRAFTS, draft)
    return {
        **draft,
        "explanation": "The merchant MCP server stored a draft and did not charge a card.",
    }


def get_eligible_discounts(user_id: str = "", product_id: str = "") -> dict:
    offer = next(
        (
            {"label": item.get("label"), "percent": item.get("percent")}
            for item in _discounts()
            if item.get("user_id") == user_id and item.get("product_id") == product_id
        ),
        None,
    )
    offers = [offer] if offer else []
    explanation = "The merchant MCP server matched one discount." if offer else "The merchant MCP server matched no discount."
    return {"product_id": product_id, "offers": offers, "explanation": explanation}


def request_approval(action: str = "", summary: str = "", approved: bool = False) -> dict:
    record = {"action": action, "summary": str(summary)[:240], "approved": approved, "submitted": False}
    _remember(REQUESTS, record)
    return {
        **record,
        "explanation": "The merchant MCP server recorded the request and sent no refund.",
    }


TOOLS = {
    "search_products": search_products,
    "get_product_details": get_product_details,
    "compare_products": compare_products,
    "check_stock": check_stock,
    "get_order_status": get_order_status,
    "prepare_order": prepare_order,
    "get_eligible_discounts": get_eligible_discounts,
    "request_approval": request_approval,
}

SCHEMAS = {
    "search_products": {"type": "object", "properties": {"query": {"type": "string"}}},
    "get_product_details": {"type": "object", "properties": {"product_id": {"type": "string"}}},
    "compare_products": {"type": "object", "properties": {"product_ids": {"type": "array"}}},
    "check_stock": {"type": "object", "properties": {"product_id": {"type": "string"}}},
    "get_order_status": {"type": "object", "properties": {"order_id": {"type": "string"}}},
    "prepare_order": {"type": "object", "properties": {"product_id": {"type": "string"}, "user_id": {"type": "string"}, "amount": {"type": "number"}, "approved": {"type": "boolean"}}},
    "get_eligible_discounts": {"type": "object", "properties": {"user_id": {"type": "string"}, "product_id": {"type": "string"}}},
    "request_approval": {"type": "object", "properties": {"action": {"type": "string"}, "summary": {"type": "string"}, "approved": {"type": "boolean"}}},
}


def tool_specs() -> list[dict]:
    return [
        {"name": name, "description": name, "inputSchema": SCHEMAS[name]}
        for name in TOOLS
    ]


def _remember(bucket: list[dict], item: dict) -> None:
    with _STATE:
        bucket.append(item)
        if len(bucket) > MAX_RECORDS:
            del bucket[:-MAX_RECORDS]


def _issue_session() -> str:
    session = secrets.token_urlsafe(24)
    with _STATE:
        if len(SESSIONS) >= 256:
            SESSIONS.pop()
        SESSIONS.add(session)
    return session


def _session_ok(session: str) -> bool:
    with _STATE:
        return session in SESSIONS


def _call(name: str, arguments: dict) -> dict:
    function = TOOLS[name]
    accepted = {key: arguments[key] for key in inspect.signature(function).parameters if key in arguments}
    payload = function(**accepted)
    return {"content": [{"type": "text", "text": json.dumps(payload)}], "isError": False}


def dispatch(message: dict, session: str) -> tuple[dict | None, str]:
    method = str(message.get("method") or "")
    request_id = message.get("id")
    if request_id is None and method.startswith("notifications/"):
        if session and not _session_ok(session):
            return {"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": "Session expired."}}, ""
        return None, ""
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    if method == "initialize":
        issued = _issue_session()
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "merchant-mcp", "version": "1.0.0"},
        }
        return {"jsonrpc": "2.0", "id": request_id, "result": result}, issued
    if not _session_ok(session):
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32001, "message": "Session expired."}}, ""
    if method == "tools/list":
        result = {"tools": tool_specs()}
    elif method == "tools/call":
        name = str(params.get("name") or "")[:80]
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        if name not in TOOLS:
            result = {"content": [{"type": "text", "text": "Unknown tool."}], "isError": True}
        else:
            result = _call(name, arguments)
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}, ""
    return {"jsonrpc": "2.0", "id": request_id, "result": result}, ""


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path.split("?", 1)[0].rstrip("/") != "/mcp":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            self.send_error(400)
            return
        if length < 0 or length > MAX_BODY:
            self.send_error(413)
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            message = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self._send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Invalid JSON"}})
            return
        if not isinstance(message, dict):
            self._send({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}})
            return
        expected = os.environ.get("MERCHANT_MCP_TOKEN", "").strip()
        header = self.headers.get("Authorization") or ""
        presented = header[7:].strip() if header.startswith("Bearer ") else ""
        if expected and (len(presented) != len(expected) or not secrets.compare_digest(presented, expected)):
            self._send(
                {"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32001, "message": "Unauthorized"}},
                status=401,
            )
            return
        response, issued = dispatch(message, self.headers.get("Mcp-Session-Id", "").strip())
        if response is None:
            self.send_response(202)
            self.end_headers()
            return
        self._send(response, session=issued)

    def log_message(self, format: str, *args) -> None:
        return

    def _send(self, payload: dict, status: int = 200, session: str = "") -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if session:
            self.send_header("Mcp-Session-Id", session)
        self.end_headers()
        self.wfile.write(body)


def make_server(host: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    host = os.environ.get("MERCHANT_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MERCHANT_MCP_PORT", "8091"))
    server = make_server(host, port)
    print(f"Merchant MCP http://{host}:{port}/mcp", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
