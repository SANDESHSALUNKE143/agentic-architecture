"""Run state, approvals, and cancellation.

Purpose: keep a run in this process so a different actor can approve it later. A second API process would not see that queue.
Used by: orchestrator/platform.py and orchestrator/workflow-engine/engine.py.
"""

from __future__ import annotations

import hashlib
import json

from shared.contracts import new_id


def digest(arguments: dict) -> str:
    raw = json.dumps(arguments, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class RunStore:
    def __init__(self) -> None:
        self.runs: dict[str, dict] = {}
        self.approvals: dict[str, dict] = {}
        self.audit: list[dict] = []

    def create(self, run: dict) -> dict:
        self.runs[run["request_id"]] = run
        return run

    def get(self, run_id: str) -> dict | None:
        return self.runs.get(run_id)

    def cancel(self, run_id: str) -> bool:
        run = self.runs.get(run_id)
        if not run or not run.get("running"):
            return False
        run["cancelled"] = True
        run["running"] = False
        run["status"] = "failed"
        return True

    def open_approval(self, run_id: str, agent_id: str, pending: dict) -> dict:
        approval = {
            "id": new_id("apr"),
            "run_id": run_id,
            "agent_id": agent_id,
            "tool": pending["name"],
            "arguments": pending.get("arguments") or {},
            "argument_hash": digest(pending.get("arguments") or {}),
            "status": "pending",
        }
        self.approvals[approval["id"]] = approval
        return approval

    def decide(self, approval_id: str, decision: str, actor: str) -> tuple[dict | None, str]:
        approval = self.approvals.get(approval_id)
        if approval is None:
            return None, "missing"
        if approval["status"] != "pending":
            return None, "not_pending"
        if actor == approval["agent_id"]:
            return None, "self_approval"
        approval["status"] = "approved" if decision == "approve" else "rejected"
        approval["actor"] = actor
        self.audit.append({"approval_id": approval_id, "decision": approval["status"], "actor": actor})
        return approval, ""
