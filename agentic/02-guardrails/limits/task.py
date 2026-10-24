"""Request size limits.

Purpose: reject a task that is too long before the router runs.
Used by: agentic/platform/composition.py at the start of a run.
"""

from __future__ import annotations

from agentic.platform.config import MAX_TASK_CHARS


def check_task_size(task: str) -> str | None:
    if not str(task).strip():
        return "Task is empty."
    if len(task) > MAX_TASK_CHARS:
        return f"Task exceeds {MAX_TASK_CHARS} characters."
    return None
