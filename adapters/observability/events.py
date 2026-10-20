"""
Content-free OpenTelemetry events for one agent run.

When OTEL_EXPORTER_OTLP_ENDPOINT is set, each run is one parent span named
agent.run. Tool spans are children. Allowed attributes are status, duration,
token counts, step count, and tool name. Prompts and answers are dropped.

Usage:
    observer = PlatformObserver("my-agent")
    runner = AgentRunner(model, tools, instruction, observer=observer)
"""

import logging
import os
import threading

# ── OTLP observer ─────────────────────────────────────────────────────


class PlatformObserver:
    """Optional OTLP traces, metrics and logs with an optional scoped SQLite sink.

    Exporters are enabled by OTEL_EXPORTER_OTLP_ENDPOINT. Events for one run share
    a parent span named agent.run. Attributes stay on the allowlist. Call close on shutdown."""

    ALLOWED = {
        "status",
        "duration_ms",
        "input_tokens",
        "output_tokens",
        "steps",
        "tool",
    }

    def __init__(self, service_name, store=None):
        self.store = store
        self.providers = []
        self.tracer = self.counter = self.logger = None
        self._runs = {}
        self._lock = threading.Lock()
        if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            return
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        tp = TracerProvider(resource=resource)
        tp.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        mp = MeterProvider(
            resource=resource,
            metric_readers=[
                PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=3000)
            ],
        )
        lp = LoggerProvider(resource=resource)
        lp.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
        self.providers = [tp, mp, lp]
        self.tracer = tp.get_tracer(service_name)
        self.counter = mp.get_meter(service_name).create_counter("agentic_events")
        self.logger = logging.Logger(service_name, logging.INFO)
        self.logger.addHandler(LoggingHandler(level=logging.INFO, logger_provider=lp))

    def emit(self, ctx, run_id, event, fields):
        """Record scoped metadata, filter content fields and enqueue configured telemetry exports."""
        if self.store:
            self.store.emit(ctx, run_id, event, fields)
        if not self.tracer:
            return
        attrs = {"tenant_id": ctx.tenant_id, "agent_id": ctx.agent_id, "event": event}
        safe = {k: v for k, v in fields.items() if k in self.ALLOWED}
        attributes = {**attrs, **safe, "run_id": run_id}
        if event == "run.started":
            parent = self.tracer.start_span("agent.run", attributes=attributes)
            with self._lock:
                self._runs[run_id] = parent
            self._signal(attrs, safe, run_id)
            return
        with self._lock:
            parent = self._runs.get(run_id)
            if event == "run.finished":
                self._runs.pop(run_id, None)
        span_name = safe.get("tool", event) if event == "tool.completed" else event
        if parent is None:
            with self.tracer.start_as_current_span(span_name, attributes=attributes):
                self._signal(attrs, safe, run_id)
            return
        from opentelemetry import trace

        with trace.use_span(parent, end_on_exit=False):
            with self.tracer.start_as_current_span(span_name, attributes=attributes):
                self._signal(attrs, safe, run_id)
        if event == "run.finished":
            for key, value in safe.items():
                parent.set_attribute(key, value)
            parent.end()

    def _signal(self, attrs, safe, run_id):
        """Count and log one allowlisted event. Missing exporters stay silent."""
        if self.counter:
            self.counter.add(1, attrs)
        if self.logger:
            self.logger.info(attrs["event"], extra={**attrs, **safe, "run_id": run_id})

    def close(self):
        """Shut down owned exporters; application shutdown must call this to flush queued events."""
        for provider in self.providers:
            provider.shutdown()
