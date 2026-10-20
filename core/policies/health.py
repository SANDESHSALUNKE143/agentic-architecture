"""
Dependency health — each optional store reports ok or degraded.

A process can serve questions while a metrics backend is down. The health
board records that split so an operator sees degraded instead of a single
boolean that hides the broken dependency. Details are short status words.
Passwords, URLs with userinfo, and document text do not belong here.

Usage:
    board = HealthBoard()
    board.set("postgres", ok=True)
    board.set("langfuse", ok=False, detail="unreachable")
    board.public()
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

# ── Board ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DependencyStatus:
    """One dependency: a name, whether it answered, and a short detail."""

    name: str
    ok: bool
    detail: str


class HealthBoard:
    """Mutable set of dependency statuses for one process."""

    def __init__(self) -> None:
        self._rows: dict[str, DependencyStatus] = {}
        self._lock = threading.Lock()

    def set(self, name: str, *, ok: bool, detail: str = "") -> None:
        """Record a dependency. The detail is a status word, not a secret or a payload."""
        if not name or any(
            mark in detail.lower() for mark in ("password", "secret", "token", "://")
        ):
            raise ValueError("health detail must be a short status with no secret and no URL")
        with self._lock:
            self._rows[name] = DependencyStatus(name, ok, detail or ("ok" if ok else "degraded"))

    def public(self) -> dict:
        """Return ok when every recorded dependency is ok, otherwise degraded."""
        rows = list(self._rows.values())
        return {
            "status": "ok"
            if rows and all(row.ok for row in rows)
            else "degraded"
            if rows
            else "ok",
            "dependencies": {row.name: {"ok": row.ok, "detail": row.detail} for row in rows},
        }
