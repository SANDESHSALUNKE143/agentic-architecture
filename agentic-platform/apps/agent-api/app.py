"""HTTP boundary. The engine does the work. This module checks the local token and the payload."""

from __future__ import annotations

import secrets

from shared.config import DEV_TOKEN, assert_runtime_config, dev_token, platform_env
from shared.contracts import RunRequest
from shared.security.limits import check_task_size

try:
    from fastapi import FastAPI, Header, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Install the API extra: python -m pip install 'fastapi>=0.115' 'uvicorn>=0.32' httpx"
    ) from exc


class RunBody(BaseModel):
    task: str = ""
    user_id: str = "local-development-user"
    workflow: str | None = None
    agents: list[str] | None = None
    example_id: str | None = None
    session_id: str = ""
    context: dict = Field(default_factory=dict)
    mode: str = "mock"


class DecisionBody(BaseModel):
    decision: str
    actor: str = "operator"


class FeedbackBody(BaseModel):
    rating: str
    note: str = ""


class NoteBody(BaseModel):
    text: str
    user_id: str = "local-development-user"


def create_app(platform=None):
    """Build the API. Tests pass a platform with a temporary data directory."""
    assert_runtime_config()
    if platform is None:
        from orchestrator.platform import Platform

        platform = Platform()

    app = FastAPI(title="Agentic platform", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def authorize(authorization: str | None) -> None:
        if platform_env() == "production" and dev_token() == DEV_TOKEN:
            raise HTTPException(401, "production rejects the default dev token")
        token = (authorization or "").removeprefix("Bearer ").strip()
        expected = dev_token()
        if (
            not authorization
            or not authorization.startswith("Bearer ")
            or not secrets.compare_digest(token, expected)
        ):
            raise HTTPException(401, "invalid credentials")

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "mock"}

    @app.get("/agents")
    def agents(authorization: str | None = Header(default=None)):
        authorize(authorization)
        return {"agents": [agent.definition() for agent in platform.agents.values()]}

    @app.get("/delegation")
    def delegation(authorization: str | None = Header(default=None)):
        authorize(authorization)
        from shared.config import ROOT
        from shared.loader import load_module

        pairs_module = load_module(
            ROOT / "workflows" / "agent-chain" / "combinations.py",
            "platform_combinations",
        )
        pairs = pairs_module.allowlisted_pairs(sorted(platform.agents))
        return {"pairs": [{"source": a, "target": b} for a, b in pairs]}

    @app.get("/examples")
    def examples(authorization: str | None = Header(default=None)):
        authorize(authorization)
        from examples.scenarios.catalog import list_examples

        return {"examples": list_examples()}

    @app.get("/tools")
    def tools(authorization: str | None = Header(default=None)):
        authorize(authorization)
        return {"tools": platform.gateway.describe()}

    @app.post("/agent-runs")
    async def create_run(body: RunBody, authorization: str | None = Header(default=None)):
        authorize(authorization)
        if body.example_id:
            from examples.scenarios.run_scenario import run_example

            try:
                return await run_example(platform, body.example_id)
            except KeyError:
                raise HTTPException(404, "unknown example") from None
        problem = check_task_size(body.task)
        if problem:
            raise HTTPException(422, problem)
        request = RunRequest(
            task=body.task,
            user_id=body.user_id,
            workflow=body.workflow,
            agents=body.agents,
            session_id=body.session_id,
            context=body.context,
            mode=body.mode,
        )
        return await platform.run(request)

    @app.get("/agent-runs/{request_id}")
    def get_run(request_id: str, authorization: str | None = Header(default=None)):
        authorize(authorization)
        stored = platform.store.get(request_id)
        if stored is None:
            raise HTTPException(404, "run not found")
        return platform.engine.public_run(stored)

    @app.post("/agent-runs/{request_id}/cancel")
    def cancel_run(request_id: str, authorization: str | None = Header(default=None)):
        authorize(authorization)
        try:
            state = platform.store.cancel(request_id)
        except KeyError:
            raise HTTPException(404, "run not found") from None
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"request_id": request_id, "status": state}

    @app.post("/agent-runs/{request_id}/feedback")
    def feedback(
        request_id: str, body: FeedbackBody, authorization: str | None = Header(default=None)
    ):
        authorize(authorization)
        try:
            return platform.feedback(request_id, body.rating, body.note)
        except KeyError:
            raise HTTPException(404, "run not found") from None
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/approvals")
    def approvals(authorization: str | None = Header(default=None)):
        authorize(authorization)
        return {"approvals": platform.store.pending()}

    @app.post("/approvals/{approval_id}/decision")
    async def decision(
        approval_id: str, body: DecisionBody, authorization: str | None = Header(default=None)
    ):
        authorize(authorization)
        try:
            return await platform.resume(approval_id, body.decision, body.actor)
        except KeyError:
            raise HTTPException(404, "approval not found") from None
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/memory/{session_id}")
    def memory(session_id: str, authorization: str | None = Header(default=None)):
        authorize(authorization)
        return {
            "session_id": session_id,
            "short_term": platform.memory.session_view(session_id),
            "notes": platform.memory.list_notes(),
        }

    @app.post("/memory/notes")
    def notes(body: NoteBody, authorization: str | None = Header(default=None)):
        authorize(authorization)
        if not body.text.strip():
            raise HTTPException(422, "text is required")
        staged = platform.memory.stage_note(body.text, body.user_id)
        approval = platform.store.open_approval(
            run_id="",
            agent_id="memory",
            action="save_note",
            summary=staged["summary"],
            params=staged["params"],
            impact="The note is stored locally after approval.",
        )
        return {"status": "needs_approval", "approval_id": approval["id"], "approval": approval}

    @app.post("/webhook/{name}")
    async def webhook(
        name: str, body: dict | None = None, authorization: str | None = Header(default=None)
    ):
        authorize(authorization)
        from workflows.n8n.mock import accept

        path = f"/webhook/{name}"
        try:
            return await accept(platform, path, body or {})
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    return app
