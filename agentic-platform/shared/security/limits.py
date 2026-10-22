"""Request size checks. The engine applies hop, tool, and time limits."""

from __future__ import annotations

from shared.config import MAX_TASK_CHARS


def check_task_size(task: str) -> str | None:
    """Return an error message when the task is empty or too large."""
    if not isinstance(task, str) or not task.strip():
        return "task must contain text"
    if len(task) > MAX_TASK_CHARS:
        return f"task exceeds {MAX_TASK_CHARS} characters"
    return None
