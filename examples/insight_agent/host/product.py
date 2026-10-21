"""
Product page and admin settings for the insight agent.

Port 8030 serves the question form to anyone on the loopback host. The
admin token is required only for reading and saving connection settings.
Passwords stay in the environment. The token is compared in memory and
is not written into the HTML.

Run: started by insight_agent.server.serve on process startup.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from insight_agent.action import execute
from insight_agent.perception import perceive

# ── Product page ──────────────────────────────────────────────────────

_PAGE = (Path(__file__).with_name("product.html")).read_text(encoding="utf-8")


def serve_product(runner, context, observer, tools, allowlists, bindings, sql, models, web) -> None:
    """
    Serve the question page and the settings API on port 8030.

    Steps:
        1. GET / and GET /health need no token.
        2. POST /ask runs the harness and returns the answer.
        3. GET and PUT /admin/connections require the bearer token.
        4. A valid PUT updates the live allowlists and stores the next revision.
    """
    from insight_agent.host.settings import apply, current_revision, store_revision

    def authorized(handler) -> bool:
        import os
        import secrets

        header = handler.headers.get("Authorization", "")
        supplied = header.removeprefix("Bearer ")
        token = os.environ["AGENT_API_TOKEN"]
        if header.startswith("Bearer ") and secrets.compare_digest(supplied, token):
            return True
        handler._send(401, b'{"detail":"invalid credentials"}', "application/json")
        return False

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            """Skip request logs so the question text is not written."""
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._send(200, b'{"status":"ok"}', "application/json")
                return
            if self.path in {"/", "/index.html"}:
                self._send(200, _PAGE.encode(), "text/html; charset=utf-8")
                return
            if self.path == "/admin/connections":
                if not authorized(self):
                    return
                payload = {
                    "revision": current_revision(),
                    "connections": bindings.public(),
                }
                self._send(200, json.dumps(payload).encode(), "application/json")
                return
            self._send(404, b'{"detail":"not found"}', "application/json")

        def do_POST(self):
            if self.path != "/ask":
                self._send(404, b'{"detail":"not found"}', "application/json")
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                question = perceive(self.rfile.read(length))
            except ValueError as exc:
                self._send(422, json.dumps({"detail": str(exc)}).encode(), "application/json")
                return
            status, payload = execute(runner, context, observer, question)
            self._send(status, json.dumps(payload).encode(), "application/json")

        def do_PUT(self):
            if self.path != "/admin/connections":
                self._send(404, b'{"detail":"not found"}', "application/json")
                return
            if not authorized(self):
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode())
            try:
                apply(bindings, sql, models, web, tools, allowlists, body)
                stored = store_revision(bindings)
            except ValueError as exc:
                self._send(422, json.dumps({"detail": str(exc)}).encode(), "application/json")
                return
            self._send(200, json.dumps(stored).encode(), "application/json")

    server = ThreadingHTTPServer(("0.0.0.0", 8030), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
