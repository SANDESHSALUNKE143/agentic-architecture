"""
Operator console API.

Lists the agents in OPERATOR_AGENTS, proxies each agent's own URL, and
serves the read-only page. The bearer token is compared with the
Authorization header and is not written into the HTML. Agent configuration
is changed on the agent's settings page. This process only reads it.

Run: uvicorn agentic_sdk.services.operator_ui.app:create_app --factory
"""

from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

_PAGE = (Path(__file__).with_name("page.html")).read_text(encoding="utf-8")


# ── Application ───────────────────────────────────────────────────────


def create_app():
    """Serve the operator page and credential-scoped agent, config, connector and run routes.

    OPERATOR_TOKEN is compared with the Authorization header. OPERATOR_AGENTS lists
    the agents that token may see. Publishing a revision does not restart agents."""
    from agentic_sdk.adapters.persistence.postgres import Database

    expected = os.environ["OPERATOR_TOKEN"]
    if len(expected) < 32:
        raise ValueError("operator token must contain at least 32 characters")
    declared = json.loads(os.environ["OPERATOR_AGENTS"])
    database = Database(os.environ["DATABASE_URL"])

    def authorize(authorization: str | None) -> None:
        """Accept only the configured bearer token. Do not reflect it in errors."""
        supplied = (authorization or "").removeprefix("Bearer ")
        if (
            not authorization
            or not authorization.startswith("Bearer ")
            or not secrets.compare_digest(supplied, expected)
        ):
            raise HTTPException(401, "invalid credentials")

    def agent_for(agent_id: str) -> dict:
        """Return the declared binding for one agent id visible to this token."""
        for item in declared:
            if item["agent_id"] == agent_id:
                return item
        raise HTTPException(404, "agent not registered")

    def proxy(binding: dict, method: str, path: str, authorization: str, payload: dict | None = None):
        """Forward a JSON call to the agent URL declared for this credential."""
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(
            binding["url"].rstrip("/") + path,
            data=data,
            headers={"Authorization": authorization, "Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try:
                detail = json.loads(raw).get("detail", "agent rejected the call")
            except json.JSONDecodeError:
                detail = "agent rejected the call"
            raise HTTPException(exc.code, detail) from None

    @asynccontextmanager
    async def lifespan(app):
        """Create prototype tables, then close nothing the agent still owns."""
        database.initialize()
        yield

    app = FastAPI(title="Agent operator", version="0.3.0", lifespan=lifespan)

    @app.get("/health")
    def health():
        """Report process readiness without disclosing credentials or config."""
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def index():
        """Return the operator page. The page does not contain a credential."""
        return _PAGE

    @app.get("/api/agents")
    def agents(authorization: str | None = Header(default=None)):
        """List tenant, agent id and permissions for the authenticated credential."""
        authorize(authorization)
        return {
            "agents": [
                {
                    "tenant_id": item["tenant_id"],
                    "agent_id": item["agent_id"],
                    "permissions": list(item["permissions"]),
                }
                for item in declared
            ]
        }

    @app.get("/api/config")
    def read_config(agent_id: str, authorization: str | None = Header(default=None)):
        """Return the latest configuration revision, or revision 0 when none exists."""
        authorize(authorization)
        binding = agent_for(agent_id)
        with database.connect() as connection:
            row = connection.execute(
                """SELECT revision, config FROM configurations
                WHERE tenant=%s AND agent=%s ORDER BY revision DESC LIMIT 1""",
                (binding["tenant_id"], agent_id),
            ).fetchone()
        if not row:
            return {"revision": 0, "config": None}
        return {"revision": row["revision"], "config": row["config"]}

    @app.put("/api/config")
    def write_config(body: dict, authorization: str | None = Header(default=None)):
        """Publish the next immutable revision or return 409 when the caller is stale."""
        authorize(authorization)
        binding = agent_for(body["agent_id"])
        expected = body["expected_revision"]
        config = body["config"]
        if type(expected) is not int or not isinstance(config, dict):
            raise HTTPException(422, "expected_revision and config object are required")
        from psycopg.types.json import Jsonb

        with database.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (binding["tenant_id"] + ":" + body["agent_id"],),
            )
            latest = connection.execute(
                "SELECT COALESCE(MAX(revision),0) AS revision FROM configurations WHERE tenant=%s AND agent=%s",
                (binding["tenant_id"], body["agent_id"]),
            ).fetchone()["revision"]
            if latest != expected:
                raise HTTPException(409, "revision conflict")
            connection.execute(
                "INSERT INTO configurations VALUES(%s,%s,%s,%s)",
                (binding["tenant_id"], body["agent_id"], latest + 1, Jsonb(config)),
            )
        return {
            "revision": latest + 1,
            "detail": "Revision stored. Publishing does not reload a running agent.",
        }

    @app.get("/api/connectors")
    def connectors(agent_id: str, authorization: str | None = Header(default=None)):
        """Return the agent tool and allowlist snapshot. This view does not edit them."""
        authorize(authorization)
        return proxy(agent_for(agent_id), "GET", "/v1/connectors", authorization)

    @app.get("/api/events")
    def events(agent_id: str, authorization: str | None = Header(default=None)):
        """Return content-free run events recorded by the agent."""
        authorize(authorization)
        return proxy(agent_for(agent_id), "GET", "/v1/events", authorization)

    @app.post("/api/runs")
    def runs(body: dict, authorization: str | None = Header(default=None)):
        """Forward one question to the agent and return its answer."""
        authorize(authorization)
        return proxy(
            agent_for(body["agent_id"]),
            "POST",
            "/v1/runs",
            authorization,
            {"question": body["question"]},
        )

    @app.get("/api/observability")
    def observability(authorization: str | None = Header(default=None)):
        """Report OpenTelemetry, MLflow, and the optional framework callers."""
        authorize(authorization)

        def reachable(url: str) -> bool:
            if not url:
                return False
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    return 200 <= response.status < 300
            except Exception:
                return False

        grafana = os.environ.get("GRAFANA_BROWSER_URL", "http://grafana.localhost:3002")
        mlflow = os.environ.get("MLFLOW_BROWSER_URL", "http://mlflow.localhost:5000")
        return {
            "backends": [
                {
                    "name": "OpenTelemetry",
                    "reachable": reachable(os.environ.get("GRAFANA_PROBE_URL", "")),
                    "optional": False,
                    "detail": "Collector, Tempo, Prometheus, Loki, and Grafana. Spans carry status, duration, tool name, and token counts. Prompts stay out.",
                    "href": grafana,
                    "link_label": "Open Grafana",
                },
                {
                    "name": "Langfuse",
                    "reachable": reachable(os.environ.get("LANGFUSE_PROBE_URL", "")),
                    "optional": False,
                    "detail": "One trace per agent run. Tool spans are children. Attributes are status, duration, tool name, and token counts. Prompts and answers stay out.",
                    "href": os.environ.get("LANGFUSE_BROWSER_URL", "http://langfuse.localhost:3003"),
                    "link_label": "Open Langfuse",
                },
                {
                    "name": "MLflow",
                    "reachable": reachable(os.environ.get("MLFLOW_PROBE_URL", "")),
                    "optional": False,
                    "detail": "Each run logs tool names, status, and duration. The question text is not a parameter.",
                    "href": mlflow,
                    "link_label": "Open MLflow",
                },
                {
                    "name": "LangChain",
                    "reachable": False,
                    "optional": True,
                    "detail": "An optional caller. A LangChain tool can invoke AgentRunner. Guardrails, identity, and telemetry stay in the SDK.",
                    "href": "",
                    "link_label": "",
                },
                {
                    "name": "LangGraph",
                    "reachable": False,
                    "optional": True,
                    "detail": "An optional caller for a later checkpointed graph. This release runs one bounded harness loop, not a graph runtime.",
                    "href": "",
                    "link_label": "",
                },
            ]
        }

    return app
