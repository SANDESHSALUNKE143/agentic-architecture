"""
Token-protected API for the insight agent.

Port 8010 is the surface the operator console calls. Every data route
requires the bearer token. The product page on port 8030 is started from
here and does not expose this token in its HTML.

Routes:
    GET  /health
    GET  /v1/connectors   tools, allowlists, servers, and control facts
    GET  /v1/events       content-free lifecycle events
    POST /v1/runs         one question through the harness

Run: insight_agent.server.serve, from python -m insight_agent.
"""

import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from insight_agent.action import execute
from insight_agent.host.product import serve_product
from insight_agent.perception import perceive

# ── Operator API ──────────────────────────────────────────────────────


def _limits(runner):
    """Describe the request gate and the per-run ceilings for the operator card."""
    limits = runner.limits
    gate = getattr(runner, "gate", None)
    view = gate.public() if gate is not None else {}
    return {
        "request_rate": (
            f"{view['request_rate_per_minute']} per minute" if view else "Not configured"
        ),
        "max_body_bytes": view.get("max_body_bytes", "Not configured"),
        "daily_token_quota": view.get("daily_tokens", "Not configured"),
        "monthly_token_quota": view.get("monthly_tokens", "Not configured"),
        "token_budget_per_run": limits.token_budget,
        "timeout_seconds": limits.timeout_seconds,
        "max_steps": limits.max_steps,
    }


def serve(runner, context, observer, tools, allowlists, bindings, sql, models, web):
    """Listen on port 8010 and require the agent bearer token on every data route."""
    token = os.environ["AGENT_API_TOKEN"]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            """Skip default request logs so question text in a path cannot be recorded."""
            return

        def _authorized(self) -> bool:
            header = self.headers.get("Authorization", "")
            supplied = header.removeprefix("Bearer ")
            if header.startswith("Bearer ") and secrets.compare_digest(supplied, token):
                return True
            self._json(401, {"detail": "invalid credentials"})
            return False

        def _json(self, status: int, payload: dict) -> None:
            raw = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path == "/health":
                self._json(200, {"status": "ok"})
                return
            if not self._authorized():
                return
            if self.path == "/v1/connectors":
                finished = [item for item in observer.events if item.get("event") == "run.finished"]
                limits = runner.limits
                self._json(
                    200,
                    {
                        "tools": [spec.public() for spec in tools._tools.values()],
                        "allowlists": allowlists,
                        "connections": bindings.public(),
                        "controls": {
                            "model": {
                                "name": "Scripted decision model",
                                "provider": "None",
                                "adapter": "scripted",
                                "detail": "No external LLM is called. Each decision reports 1 input token and 1 output token to the harness.",
                            },
                            "usage": {
                                "runs": len(finished),
                                "succeeded": sum(
                                    1 for item in finished if item.get("status") == "ok"
                                ),
                                "rejected": sum(
                                    1 for item in finished if item.get("status") != "ok"
                                ),
                                "input_tokens": sum(
                                    item.get("input_tokens") or 0 for item in finished
                                ),
                                "output_tokens": sum(
                                    item.get("output_tokens") or 0 for item in finished
                                ),
                            },
                            "guardrails": [
                                "Evidence required before an answer: "
                                + ", ".join(sorted(runner.required_before_final)),
                                "Call permissions: " + ", ".join(sorted(context.permissions)),
                                "SQL reads are allowlisted and read only",
                                "The model cannot supply credentials, URLs, permissions, or mutation approval",
                                "An identical tool call is rejected",
                            ],
                            "harness": {
                                "max_steps": limits.max_steps,
                                "timeout_seconds": limits.timeout_seconds,
                                "token_budget": limits.token_budget,
                                "max_output_tokens": limits.max_output_tokens,
                                "max_context_bytes": limits.max_context_bytes,
                                "max_tool_result_bytes": limits.max_tool_result_bytes,
                            },
                            "governance": [
                                "Tenant " + context.tenant_id + ", agent " + context.agent_id,
                                "Access uses the operator bearer token",
                                "Configuration is saved by the agent. This console is read only",
                            ],
                            "limits": _limits(runner),
                        },
                    },
                )
                return
            if self.path == "/v1/events":
                self._json(200, {"events": observer.events})
                return
            self._json(404, {"detail": "not found"})

        def do_POST(self):
            if self.path != "/v1/runs":
                self._json(404, {"detail": "not found"})
                return
            if not self._authorized():
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                question = perceive(self.rfile.read(length))
            except ValueError as exc:
                self._json(422, {"detail": str(exc)})
                return
            status, payload = execute(runner, context, observer, question)
            self._json(status, payload)

    serve_product(runner, context, observer, tools, allowlists, bindings, sql, models, web)
    ThreadingHTTPServer(("0.0.0.0", 8010), Handler).serve_forever()
