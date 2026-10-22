"""Request size limits."""

from __future__ import annotations

from shared.config import MAX_TASK_CHARS


def check_task_size(task: str) -> str | None:
    if not str(task).strip():
        return "Task is empty."
    if len(task) > MAX_TASK_CHARS:
        return f"Task exceeds {MAX_TASK_CHARS} characters."
    return None
