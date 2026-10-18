"""Model admission control, decision forwarding and durable token usage queries."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict

from agentic_sdk.services.contracts import Decision
from fastapi import Header, HTTPException


def register(app, db, embedder, store, auth, observer):
    """Register decision and usage routes with atomic daily reservations before model invocation."""

    @app.post("/v1/models/decide")
    def decide(body: Decision, authorization: str | None = Header(default=None)):
        """Reserve daily tokens before a synthetic or compatible model call and record reported usage."""
        ctx = auth(authorization, "model:invoke")
        encoded = json.dumps(body.model_dump()).encode()
        if len(encoded) > 100000:
            raise HTTPException(413, "model context too large")
        db.reserve(
            ctx,
            len(encoded) + body.max_output_tokens + 512,
            int(os.getenv("DAILY_TOKEN_LIMIT", "1000000")),
        )
        from agentic_sdk.execution import ModelReply

        if os.getenv("MODEL_MODE", "demo") == "demo":
            names = {t.get("name") for t in body.tools}
            used = {o.get("tool") for o in body.observations}
            needed = [n for n in ("list_tables", "get_data_status") if n in names and n not in used]
            action = (
                {"type": "tool", "tool": needed[0], "arguments": {}}
                if needed
                else {
                    "type": "final",
                    "answer": "DEMO readiness workflow: synthetic platform data is ready. Not a live business answer.",
                }
            )
            reply = ModelReply(action)
        else:
            import asyncio

            from agentic_sdk.project import ProjectConfig, build_model

            config = ProjectConfig.from_dict(
                {
                    "schema_version": 2,
                    "tenant_id": ctx.tenant_id,
                    "agent_id": ctx.agent_id,
                    "model": {
                        "adapter": "compatible",
                        "base_url": os.environ["MODEL_BASE_URL"],
                        "model": os.environ["MODEL_DEPLOYMENT"],
                        "api_key_env": "MODEL_API_KEY",
                    },
                    "limits": {},
                }
            )
            model = build_model(config, lambda: None)
            try:
                reply = asyncio.run(
                    model.decide(
                        body.instruction,
                        body.question,
                        body.observations,
                        body.tools,
                        body.max_output_tokens,
                    )
                )
            finally:
                model.llm.client.close()
        db.usage(ctx, reply.input_tokens, reply.output_tokens)
        observer.emit(
            ctx,
            uuid.uuid4().hex,
            "model.completed",
            {
                "status": "ok",
                "input_tokens": reply.input_tokens,
                "output_tokens": reply.output_tokens,
            },
        )
        return asdict(reply)

    @app.get("/v1/cost/usage")
    def usage(authorization: str | None = Header(default=None)):
        """Read up to 31 days of scoped reservations and reported token counts."""
        ctx = auth(authorization, "cost:read")
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT day,reserved,input_tokens,output_tokens,calls FROM token_ledger WHERE tenant=%s AND agent=%s ORDER BY day DESC LIMIT 31",
                (ctx.tenant_id, ctx.agent_id),
            ).fetchall()
        return {
            "usage": rows,
            "unit": "tokens",
            "reservation_policy": "conservative; failed calls are not refunded",
        }
