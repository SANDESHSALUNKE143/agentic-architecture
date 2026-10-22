"""In-memory runs and the approval audit. Notes and learning live on disk."""

from __future__ import annotations

from typing import Any

from shared.contracts import digest, new_id


class RunStore:
    """Process-local runs. Restarting the API clears them."""

    def __init__(self) -> None:
        self.runs: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, dict[str, Any]] = {}
        self._cancelled: set[str] = set()

    def save(self, run: dict[str, Any]) -> dict[str, Any]:
        self.runs[run["request_id"]] = run
        return run

    def get(self, request_id: str) -> dict[str, Any] | None:
        return self.runs.get(request_id)

    def cancel(self, request_id: str) -> str:
        """Mark an in-flight run. A finished run is left as it is."""
        run = self.runs.get(request_id)
        if run is None:
            raise KeyError(request_id)
        if not run.get("running"):
            raise ValueError(f"run is {run.get('status')}")
        self._cancelled.add(request_id)
        return "cancelling"

    def is_cancelled(self, request_id: str) -> bool:
        return request_id in self._cancelled

    def open_approval(
        self,
        *,
        run_id: str,
        agent_id: str,
        action: str,
        summary: str,
        params: dict[str, Any],
        impact: str,
    ) -> dict[str, Any]:
        record = {
            "id": new_id("appr"),
            "run_id": run_id,
            "agent_id": agent_id,
            "action": action,
            "summary": summary,
            "impact": impact,
            "params": params,
            "params_hash": digest(params),
            "status": "pending",
            "actor": "",
            "audit": [{"event": "requested", "agent_id": agent_id}],
        }
        self.approvals[record["id"]] = record
        return record

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        return self.approvals.get(approval_id)

    def pending(self) -> list[dict[str, Any]]:
        return [row for row in self.approvals.values() if row["status"] == "pending"]

    def decide(self, approval_id: str, decision: str, actor: str) -> dict[str, Any]:
        """Human decision. The requesting agent cannot approve itself."""
        record = self.approvals.get(approval_id)
        if record is None:
            raise KeyError(approval_id)
        if actor.strip() == record["agent_id"]:
            raise PermissionError("An agent cannot approve its own action.")
        if decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected")
        if record["status"] != "pending":
            raise ValueError(f"approval is {record['status']}")
        if digest(record["params"]) != record["params_hash"]:
            record["status"] = "stale"
            record["audit"].append({"event": "stale", "actor": actor})
            return record
        record["status"] = decision
        record["actor"] = actor
        record["audit"].append({"event": decision, "actor": actor})
        return record

    def mark_stale(self, approval_id: str) -> dict[str, Any]:
        record = self.approvals[approval_id]
        record["params_hash"] = "changed"
        record["status"] = "stale"
        record["audit"].append({"event": "stale", "actor": "system"})
        return record
