"""
Content-free trace for one agent process.

The harness emits lifecycle events. This module keeps tool name, status,
duration, and token counts. Question text, answers, and tool payloads are
rejected so they cannot land in the operator event list.

Usage:
    trace = TraceObserver()
    observer = Fanout([trace, platform_observer])
"""


# ── Fan-out ───────────────────────────────────────────────────────────


class Fanout:
    """Send one lifecycle event to every configured sink."""

    def __init__(self, observers):
        self.observers = tuple(observers)

    def emit(self, ctx, run_id, event, fields):
        """Forward the event. A sink that rejects content must still be allowed to raise."""
        for observer in self.observers:
            observer.emit(ctx, run_id, event, fields)


# ── In-memory event list ──────────────────────────────────────────────


class TraceObserver:
    """In-memory RunObserver for the operator event list."""

    def __init__(self):
        self.events = []

    def emit(self, ctx, run_id, event, fields):
        """Record lifecycle metadata for one run. Reject content fields."""
        record = {
            "event": event,
            "run_id": run_id,
            "tenant_id": ctx.tenant_id,
            "agent_id": ctx.agent_id,
        }
        record.update(fields)
        if "question" in record or "answer" in record or "result" in record:
            raise RuntimeError("observer must stay content-free")
        self.events.append(record)
