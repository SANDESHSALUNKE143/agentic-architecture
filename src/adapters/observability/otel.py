"""Optional traces/metrics bridge; exporter lifecycle belongs to the application."""

from agentic_sdk.adapters.local import SafeTelemetry


class OTelTelemetry:
    """RAG trace/metric bridge using the application-configured global OTel providers."""

    def __init__(self):
        from opentelemetry import metrics, trace

        from agentic_sdk import __version__

        self.tracer = trace.get_tracer("agentic-sdk", __version__)
        meter = metrics.get_meter("agentic-sdk", __version__)
        self.requests = meter.create_counter("agent_requests")
        self.duration = meter.create_histogram("agent_duration_ms")

    def record(self, ctx, event, fields):
        """Emit an allowlisted span, request counter and optional duration observation."""
        attrs = {"tenant_id": ctx.tenant_id, "agent_id": ctx.agent_id}
        safe = {k: v for k, v in fields.items() if k in SafeTelemetry.ALLOWED}
        with self.tracer.start_as_current_span(event, attributes={**attrs, **safe}):
            self.requests.add(1, {**attrs, "status": str(safe.get("status", "unknown"))})
            if "duration_ms" in safe:
                self.duration.record(float(safe["duration_ms"]), attrs)
