"""Content-free run telemetry with optional OTLP traces, metrics and logs."""

import logging
import os


class PlatformObserver:
    """Optional OTLP traces, metrics and logs with an optional scoped SQLite sink.

    Exporters are enabled by OTEL_EXPORTER_OTLP_ENDPOINT. Each event is a span;
    this is not a continuously propagated cross-service trace. Call close on shutdown."""

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
        with self.tracer.start_as_current_span(
            event, attributes={**attrs, **safe, "run_id": run_id}
        ):
            self.counter.add(1, attrs)
            self.logger.info(event, extra={**attrs, **safe, "run_id": run_id})

    def close(self):
        """Shut down owned exporters; application shutdown must call this to flush queued events."""
        for provider in self.providers:
            provider.shutdown()
