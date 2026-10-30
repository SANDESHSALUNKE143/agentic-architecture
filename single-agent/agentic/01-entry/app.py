"""HTTP API for one agent.

Purpose: health and one run route. The harness is desk-agent. There is no workflow list.
Used by: agentic/01-entry/main.py and the API tests.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from jobs.queue.runs import BACKGROUND
from response.contracts import AgentRequest

from agentic.platform.composition import Platform
from agentic.platform.config import assert_runtime_config
from agentic.platform.loader import load_module

assert_runtime_config()
platform = Platform()
app = FastAPI(title="Single agent", version="1.0.0", description="One agent. One harness. The written list is docs/api.md.")

_ENTRY = Path(__file__).resolve().parent
load_module(_ENTRY.parent / "02-guardrails" / "limits" / "guard.py", "agent_api_guard").install(app)
_bodies = load_module(_ENTRY / "bodies.py", "single_agent_bodies")
_auth = load_module(_ENTRY.parent / "02-guardrails" / "auth" / "auth.py", "single_agent_auth")
logger = logging.getLogger("agentic.runs")


@app.get("/health", tags=["Health"], summary="Process status")
def health(authorization: str | None = Header(default=None)):
    _auth.authorized(authorization)
    return platform.health()


@app.get("/settings/harness", tags=["Settings"], summary="The harness the next run will use")
def get_harness(authorization: str | None = Header(default=None)):
    _auth.authorized(authorization)
    return platform.harness_settings()


@app.put("/settings/harness", tags=["Settings"], summary="Choose langchain, claude, or deepagent")
def put_harness(body: _bodies.HarnessBody, authorization: str | None = Header(default=None)):
    _auth.authorized(authorization)
    try:
        return platform.set_harness(body.harness)
    except ValueError:
        raise HTTPException(status_code=422, detail="harness must be langchain, claude, or deepagent") from None


@app.post("/agent-runs", tags=["Runs"], summary="Run desk-agent")
def start_run(body: _bodies.RunBody, authorization: str | None = Header(default=None)):
    _auth.authorized(authorization)
    return platform.start(_request(body))


@app.post("/agent-runs/stream", tags=["Runs"], summary="Run desk-agent and stream each step")
async def stream_run(body: _bodies.RunBody, authorization: str | None = Header(default=None)):
    _auth.authorized(authorization)
    request = _request(body)
    import asyncio

    loop = asyncio.get_running_loop()
    events_queue: asyncio.Queue = asyncio.Queue()

    def emit(payload: dict) -> None:
        loop.call_soon_threadsafe(events_queue.put_nowait, payload)

    def work() -> None:
        try:
            emit({"type": "activity", "message": BACKGROUND})
            result = platform.start(request, on_event=emit)
            emit({"type": "done", "run": result})
        except Exception:
            logger.warning("run stream failed")
            emit({"type": "error", "message": "The run failed."})
        finally:
            loop.call_soon_threadsafe(events_queue.put_nowait, None)

    if not platform.run_queue.submit(work):
        raise HTTPException(status_code=503, detail="The work queue is full.")

    async def events():
        while True:
            item = await events_queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


def _request(body) -> AgentRequest:
    return AgentRequest(task=body.task, user_id=body.user_id, session_id=body.session_id)
