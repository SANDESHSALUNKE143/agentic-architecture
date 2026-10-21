"""Allowlisted AgentN tool API with synthetic or approved backend transport."""

from __future__ import annotations

import os
import uuid

from agentic_sdk.services.contracts import ToolCall
from fastapi import Header, HTTPException


def register(app, db, embedder, store, auth, observer):
    """Register the fixed AgentN tool allowlist; never accept caller-selected URLs or credentials."""

    @app.post("/v1/tools/{name}")
    def tool(name: str, body: ToolCall, authorization: str | None = Header(default=None)):
        """Authorize and execute a server-allowlisted tool; the backend retains business-data authorization."""
        ctx = auth(authorization, "tools:invoke")
        # The local platform only exposes trusted read-only AgentN tools.
        if name not in {"list_tables", "get_data_status", "execute_sql"}:
            raise HTTPException(404, "tool not registered")
        if os.getenv("BACKEND_MODE", "demo") == "demo":
            if body.arguments and name != "execute_sql":
                raise HTTPException(422, "unexpected arguments")
            if name == "list_tables":
                result = {
                    "data": {
                        "views": [
                            {
                                "name": "delivery_daily",
                                "columns": [{"name": "impressions"}, {"name": "spend"}],
                            }
                        ]
                    }
                }
            elif name == "get_data_status":
                result = {
                    "ready": True,
                    "data_version": "synthetic-platform-v1",
                    "warnings": [],
                }
            else:
                if (
                    set(body.arguments) != {"sql"}
                    or not isinstance(body.arguments["sql"], str)
                    or not 1 <= len(body.arguments["sql"]) <= 8000
                ):
                    raise HTTPException(422, "invalid SQL arguments")
                result = {
                    "data": {
                        "columns": ["impressions", "spend"],
                        "rows": [[10000, 125]],
                        "truncated": False,
                    },
                    "synthetic": True,
                }
        else:
            # Fixed endpoint and credential binding. Caller cannot choose URLs or bearer token.
            import asyncio

            from agentic_sdk.http import JsonTransport

            async def invoke():
                transport = JsonTransport(
                    os.environ["AGENTN_BASE_URL"],
                    lambda: os.environ["AGENTN_ACCESS_TOKEN"],
                )
                try:
                    path = {
                        "list_tables": "catalog",
                        "get_data_status": "status",
                        "execute_sql": "sql",
                    }[name]
                    if name != "execute_sql" and body.arguments:
                        raise HTTPException(422, "unexpected arguments")
                    return await transport.request(
                        "POST" if name == "execute_sql" else "GET",
                        "/api/agent/" + path,
                        body=body.arguments if name == "execute_sql" else None,
                    )
                finally:
                    await transport.aclose()

            result = asyncio.run(invoke())
        observer.emit(ctx, uuid.uuid4().hex, "tool.completed", {"status": "ok", "tool": name})
        return result
