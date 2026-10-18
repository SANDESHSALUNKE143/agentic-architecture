"""Persistent content-free run telemetry for a single-host prototype."""

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


class SQLiteRunStore:
    """Single-host, tenant/agent-scoped metadata store with WAL-mode SQLite.

    Only approved event fields are persisted; prompts, answers and tool payloads
    are excluded. Applications own retention, backup and file access controls."""

    ALLOWED = {
        "status",
        "duration_ms",
        "input_tokens",
        "output_tokens",
        "steps",
        "tool",
    }

    def __init__(self, path: str):
        self.path = str(Path(path).resolve())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS run_events (id INTEGER PRIMARY KEY, tenant TEXT NOT NULL, agent TEXT NOT NULL, run TEXT NOT NULL, event TEXT NOT NULL, created REAL NOT NULL, fields TEXT NOT NULL)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS run_scope ON run_events(tenant,agent,id)")

    @contextmanager
    def connection(self):
        """Open a transaction and always close its connection; roll back on exceptions."""
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def emit(self, ctx, run_id, event, fields):
        """Persist allowlisted fields for a scoped run without conversation content."""
        safe = {k: v for k, v in fields.items() if k in self.ALLOWED}
        with self.connection() as db:
            db.execute(
                "INSERT INTO run_events(tenant,agent,run,event,created,fields) VALUES(?,?,?,?,?,?)",
                (
                    ctx.tenant_id,
                    ctx.agent_id,
                    run_id,
                    event,
                    time.time(),
                    json.dumps(safe),
                ),
            )

    def recent(self, ctx, limit=100):
        """Require telemetry:read and return the newest scoped events with a bounded limit."""
        ctx.require("telemetry:read")
        if not 1 <= limit <= 1000:
            raise ValueError("invalid limit")
        with self.connection() as db:
            rows = db.execute(
                "SELECT run,event,created,fields FROM run_events WHERE tenant=? AND agent=? ORDER BY id DESC LIMIT ?",
                (ctx.tenant_id, ctx.agent_id, limit),
            ).fetchall()
        return [
            {"run_id": r[0], "event": r[1], "created": r[2], "fields": json.loads(r[3])}
            for r in rows
        ]
