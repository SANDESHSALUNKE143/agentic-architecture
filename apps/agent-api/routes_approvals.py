"""Approval routes.

Purpose: list paused writes and let a different actor approve or reject one.
Used by: apps/agent-api/app.py. The Approvals page calls these routes.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Header, HTTPException
from shared.loader import load_module

_HERE = Path(__file__).resolve().parent
_bodies = load_module(_HERE / "bodies.py", "agent_api_bodies")
_auth = load_module(_HERE / "auth.py", "agent_api_auth")


def mount(app, platform) -> None:
    @app.get("/approvals", tags=["Approvals"], summary="Paused writes waiting for a decision")
    def approvals(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return list(platform.store.approvals.values())

    @app.post("/approvals/{approval_id}/decision", tags=["Approvals"], summary="Approve or reject a paused write")
    def decide(approval_id: str, body: _bodies.DecisionBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        run, error = platform.resume(approval_id, body.decision, body.actor)
        if error == "self_approval":
            raise HTTPException(status_code=403, detail="The actor cannot approve their own agent")
        if error:
            raise HTTPException(status_code=409, detail=error)
        return run
