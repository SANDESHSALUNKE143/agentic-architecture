"""
MLflow run log for the insight agent.

One finished or rejected run becomes one MLflow run: agent id, tool names,
status, and duration. The question and the answer are not parameters.
A tracking failure is swallowed so the agent answer still returns.

Run: called from insight_agent.learning.note after each question.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

# ── Public record ─────────────────────────────────────────────────────


def record(run_id: str, tools: list[str], status: str, duration_ms: float) -> None:
    """Create one MLflow run with tool names, status, and duration."""
    base = os.environ.get("MLFLOW_TRACKING_URI", "").rstrip("/")
    if not base:
        return
    try:
        experiment = _experiment_id(base)
        created = _post(
            base + "/api/2.0/mlflow/runs/create",
            {"experiment_id": experiment, "run_name": run_id},
        )
        mlflow_run = created["run"]["info"]["run_id"]
        now = int(time.time() * 1000)
        _post(
            base + "/api/2.0/mlflow/runs/log-batch",
            {
                "run_id": mlflow_run,
                "metrics": [
                    {"key": "duration_ms", "value": float(duration_ms), "timestamp": now, "step": 0}
                ],
                "params": [
                    {"key": "agent_id", "value": "insight-agent"},
                    {"key": "tools", "value": ",".join(tools)[:500]},
                    {"key": "status", "value": status},
                ],
            },
        )
        _post(
            base + "/api/2.0/mlflow/runs/update",
            {
                "run_id": mlflow_run,
                "status": "FINISHED" if status == "ok" else "FAILED",
                "end_time": now,
            },
        )
    except Exception:
        return


# ── Tracking server calls ─────────────────────────────────────────────


def _experiment_id(base: str) -> str:
    """Reuse the insight-agent experiment, creating it on the first run."""
    name = os.environ.get("MLFLOW_EXPERIMENT", "insight-agent")
    query = urllib.parse.urlencode({"experiment_name": name})
    try:
        found = _get(base + "/api/2.0/mlflow/experiments/get-by-name?" + query)
        return found["experiment"]["experiment_id"]
    except urllib.error.HTTPError:
        created = _post(base + "/api/2.0/mlflow/experiments/create", {"name": name})
        return created["experiment_id"]


def _get(url: str) -> dict:
    """Read one JSON document from the tracking server."""
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode())


def _post(url: str, payload: dict) -> dict:
    """Send one JSON body to the tracking server."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode())
