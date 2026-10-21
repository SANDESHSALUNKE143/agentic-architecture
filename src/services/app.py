"""Local platform composition and credential binding; route behavior lives in service modules."""

from __future__ import annotations

import json
import os
import secrets
from contextlib import asynccontextmanager

from agentic_sdk.contracts import Context
from agentic_sdk.services.knowledge_service.components import components
from fastapi import FastAPI, HTTPException


def create_app():
    """Compose local platform services and fixed credential-to-scope bindings.

    Startup initializes PostgreSQL; shutdown closes Qdrant and telemetry exporters.
    Only approved deployment configuration controls identities and provider routes."""
    db, embedder, store = components()
    from agentic_sdk.observation import PlatformObserver

    observer = PlatformObserver("agentic-platform")
    # Per-agent credentials are deployment configuration, never caller-provided identity.
    bindings = json.loads(os.environ["PLATFORM_BINDINGS"])
    if os.getenv("MODEL_MODE", "demo") not in {"demo", "compatible"} or os.getenv(
        "BACKEND_MODE", "demo"
    ) not in {"demo", "rest"}:
        raise ValueError("unsupported model/backend mode")
    if (
        os.getenv("BACKEND_MODE") == "rest"
        and len([b for b in bindings if "tools:invoke" in b["permissions"]]) != 1
    ):
        raise ValueError(
            "a shared live backend credential must bind exactly one tool-calling identity"
        )
    tokens = [os.environ[b["token_env"]] for b in bindings]
    if not bindings or any(len(t) < 32 for t in tokens) or len(tokens) != len(set(tokens)):
        raise ValueError("unique strong per-agent tokens required")

    def auth(authorization, permission):
        """Resolve a bearer credential to a fixed trusted context and enforce the required permission."""
        token = (authorization or "").removeprefix("Bearer ")
        for b, expected in zip(bindings, tokens):
            if (
                authorization
                and authorization.startswith("Bearer ")
                and secrets.compare_digest(token.encode(), expected.encode())
            ):
                ctx = Context(b["tenant_id"], b["agent_id"], frozenset(b["permissions"]))
                if permission not in ctx.permissions:
                    raise HTTPException(403, "permission denied")
                return ctx
        raise HTTPException(401, "invalid credentials")

    @asynccontextmanager
    async def lifespan(app):
        """Own application startup and close the configured clients/exporters at shutdown."""
        db.initialize()
        yield
        store.client.close()
        observer.close()

    app = FastAPI(title="Agentic local platform", version="0.3.0", lifespan=lifespan)

    @app.exception_handler(Exception)
    async def sanitized_error(request, exc):
        """Return a generic dependency error without disclosing upstream bodies or credentials."""
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=502,
            content={"detail": "platform dependency failed; inspect operator diagnostics"},
        )

    @app.get("/health")
    def health():
        """Probe configured dependencies and return the public readiness state."""
        with db.connect() as connection:
            connection.execute("SELECT 1")
        store.client.get_collections()
        return {"status": "ok", "embedding_profile": embedder.profile.fingerprint}

    from agentic_sdk.services.agent_registry.routes import (
        register as register_agent_registry,
    )

    register_agent_registry(app, db, embedder, store, auth, observer)
    from agentic_sdk.services.knowledge_service.routes import (
        register as register_knowledge_service,
    )

    register_knowledge_service(app, db, embedder, store, auth, observer)
    from agentic_sdk.services.model_gateway.routes import (
        register as register_model_gateway,
    )

    register_model_gateway(app, db, embedder, store, auth, observer)
    from agentic_sdk.services.tool_gateway.routes import (
        register as register_tool_gateway,
    )

    register_tool_gateway(app, db, embedder, store, auth, observer)
    return app
