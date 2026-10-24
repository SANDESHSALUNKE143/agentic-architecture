"""Run routes.

Purpose: start, stream, read, cancel, and score a run.
Used by: apps/agent-api/app.py. Chat calls the stream route.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import Header, HTTPException
from fastapi.responses import StreamingResponse
from shared.contracts import AgentRequest
from shared.loader import load_module

logger = logging.getLogger("agentic.runs")

_HERE = Path(__file__).resolve().parent
_bodies = load_module(_HERE / "bodies.py", "agent_api_bodies")
_auth = load_module(_HERE / "auth.py", "agent_api_auth")


def mount(app, platform) -> None:
    @app.post("/agent-runs", tags=["Runs"], summary="Run a task to completion")
    def start_run(body: _bodies.RunBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return platform.start(_request(body))

    @app.post("/agent-runs/stream", tags=["Runs"], summary="Run a task and stream each step")
    async def stream_run(body: _bodies.RunBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        request = _request(body)

        async def events():
            import asyncio

            loop = asyncio.get_running_loop()
            queue: asyncio.Queue = asyncio.Queue()

            def emit(payload: dict) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, payload)

            def work() -> None:
                try:
                    result = platform.start(request, on_event=emit)
                    emit({"type": "done", "run": result})
                except Exception:
                    logger.warning("run stream failed")
                    emit({"type": "error", "message": "The run failed."})
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            loop.run_in_executor(None, work)
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
                await asyncio.sleep(0.12)

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/agent-runs/{run_id}", tags=["Runs"], summary="Read one stored run")
    def get_run(run_id: str, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        run = platform.store.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return platform.public_run(run)

    @app.post("/agent-runs/{run_id}/cancel", tags=["Runs"], summary="Ask a running plan to stop")
    def cancel_run(run_id: str, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        if not platform.store.cancel(run_id):
            raise HTTPException(status_code=409, detail="Run is not running")
        return {"status": "cancelling"}

    @app.post("/agent-runs/{run_id}/feedback", tags=["Runs"], summary="Record whether the answer helped")
    def feedback(run_id: str, body: _bodies.FeedbackBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        platform.evaluation.add_feedback(run_id, body.helpful, body.note)
        return {"status": "recorded"}


def _request(body) -> AgentRequest:
    return AgentRequest(
        task=body.task,
        user_id=body.user_id,
        session_id=body.session_id,
        workflow=body.workflow,
        agents=body.agents,
    )
