"""Immutable configuration publication and scoped revision lookup."""

from __future__ import annotations

from agentic_sdk.services.contracts import Registration
from fastapi import Header, HTTPException


def register(app, db, embedder, store, auth, observer):
    """Register immutable configuration publication and revision reads with scope authorization."""

    @app.put("/v1/registry/config")
    def put_config(body: Registration, authorization: str | None = Header(default=None)):
        """Publish one immutable revision; require matching identity and reject stale writes with 409."""
        from agentic_sdk.project import ProjectConfig

        ctx = auth(authorization, "registry:write")
        try:
            config = ProjectConfig.from_dict(body.config)
        except (TypeError, ValueError):
            raise HTTPException(422, "invalid project configuration")
        if (config.tenant_id, config.agent_id) != (ctx.tenant_id, ctx.agent_id):
            raise HTTPException(403, "identity mismatch")
        # ProjectConfig accepts secret references, never a literal credential field.
        from psycopg.types.json import Jsonb

        with db.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (ctx.tenant_id + ":" + ctx.agent_id,),
            )
            latest = connection.execute(
                "SELECT COALESCE(MAX(revision),0) AS revision FROM configurations WHERE tenant=%s AND agent=%s",
                (ctx.tenant_id, ctx.agent_id),
            ).fetchone()["revision"]
            if latest != body.expected_revision:
                raise HTTPException(409, "revision conflict")
            connection.execute(
                "INSERT INTO configurations VALUES(%s,%s,%s,%s)",
                (ctx.tenant_id, ctx.agent_id, latest + 1, Jsonb(body.config)),
            )
        return {"revision": latest + 1}

    @app.get("/v1/registry/config")
    def get_config(revision: int | None = None, authorization: str | None = Header(default=None)):
        """Read the latest or explicitly requested configuration revision for the credential scope."""
        ctx = auth(authorization, "registry:read")
        with db.connect() as connection:
            row = connection.execute(
                """SELECT revision,config FROM configurations WHERE tenant=%s AND agent=%s
                AND (%s::integer IS NULL OR revision=%s) ORDER BY revision DESC LIMIT 1""",
                (ctx.tenant_id, ctx.agent_id, revision, revision),
            ).fetchone()
        if not row:
            raise HTTPException(404, "configuration not registered")
        return row
