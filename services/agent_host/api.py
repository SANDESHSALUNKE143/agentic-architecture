"""Optional reusable HTTP surface; business agents supply bindings, not route copies."""

from __future__ import annotations

import asyncio
import hashlib
import secrets
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from typing import Awaitable, Callable

from agentic_sdk.contracts import Context

from agentic_sdk.execution import AgentRunner, ExecutionError
from agentic_sdk.http import RemoteError


@dataclass
class AgentBinding:
    """Trusted mapping of one context, runner, bearer credential and shutdown callback."""

    context: Context
    runner: AgentRunner
    access_token: str
    public_config: dict
    close: Callable[[], Awaitable[None]]


def create_app(bindings: dict[str, AgentBinding], store, *, max_concurrency=4):
    """Build the reusable agent API with static credentials and per-agent concurrency caps.

    Binding keys must match their agent context. Requests cannot supply their own
    identity. Shutdown invokes each binding cleanup callback. This is not OIDC federation."""
    from fastapi import FastAPI, Header, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, ConfigDict, Field

    if not bindings or not 1 <= max_concurrency <= 64:
        raise ValueError("bindings and bounded concurrency required")
    for key, binding in bindings.items():
        if (
            key != binding.context.agent_id
            or len(binding.access_token) < 32
            or binding.access_token.startswith("replace-")
        ):
            raise ValueError(
                "binding identity must match; random token of at least 32 characters required"
            )
    gates = {key: asyncio.Semaphore(max_concurrency) for key in bindings}

    @asynccontextmanager
    async def lifespan(app):
        """Own application startup and close the configured clients/exporters at shutdown."""
        try:
            yield
        finally:
            for binding in bindings.values():
                await binding.close()

    app = FastAPI(title="Agentic Foundation API", version="0.3.0", lifespan=lifespan)

    def authorize(agent_id, authorization):
        """Resolve the requested binding and reject invalid credentials without disclosing other agents."""
        b = bindings.get(agent_id)
        supplied = (authorization or "").removeprefix("Bearer ")
        # No tenant/agent supplied in a request body can replace this binding.
        if (
            b is None
            or not authorization
            or not authorization.startswith("Bearer ")
            or not secrets.compare_digest(supplied.encode(), b.access_token.encode())
        ):
            raise HTTPException(401, "invalid credentials or agent")
        return b

    class AskRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        question: str = Field(min_length=1, max_length=8000)

    # Resolve the local request model before FastAPI inspects annotations.
    async def ask(agent_id: str, body, authorization: str | None = Header(default=None)):
        """Authorize and admit an agent run, translating expected execution failures to HTTP statuses."""
        binding = authorize(agent_id, authorization)
        gate = gates[agent_id]
        try:
            await asyncio.wait_for(gate.acquire(), timeout=0.05)
        except TimeoutError:
            raise HTTPException(
                429, "agent concurrency limit reached", headers={"Retry-After": "1"}
            )
        try:
            result = await binding.runner.run(binding.context, body.question)
            return asdict(result)
        except PermissionError:
            raise HTTPException(403, "tool permission denied") from None
        except TimeoutError:
            raise HTTPException(504, "run deadline exceeded") from None
        except RemoteError:
            raise HTTPException(502, "upstream unavailable or request rejected") from None
        except (ValueError, ExecutionError):
            raise HTTPException(422, "run rejected by validation or execution limits") from None
        except Exception:
            raise HTTPException(500, "run failed; inspect scoped telemetry") from None
        finally:
            gate.release()

    ask.__annotations__["body"] = AskRequest
    app.post("/v1/agents/{agent_id}/runs")(ask)

    @app.get("/health")
    async def health():
        """Probe configured dependencies and return the public readiness state."""
        return {"status": "ok", "version": "0.3.0"}

    @app.get("/v1/agents/{agent_id}/config")
    async def config(agent_id: str, authorization: str | None = Header(default=None)):
        """Return a sanitized binding snapshot and deterministic content revision."""
        binding = authorize(agent_id, authorization)
        import json

        value = {
            "agent_id": agent_id,
            "tenant_id": binding.context.tenant_id,
            "limits": asdict(binding.runner.limits),
            **binding.public_config,
        }
        revision = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
        return JSONResponse({"revision": revision, "config": value}, headers={"ETag": revision})

    @app.get("/v1/agents/{agent_id}/events")
    async def events(agent_id: str, authorization: str | None = Header(default=None)):
        """Read run metadata restricted to the authenticated binding context."""
        binding = authorize(agent_id, authorization)
        return {"events": store.recent(binding.context)}

    return app
