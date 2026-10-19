"""In-process integrations with real optional libraries; no paid/network calls."""

import importlib.util
import unittest
from dataclasses import replace

from agentic_sdk.adapters.local import HashEmbedder
from agentic_sdk.contracts import Context, Document


@unittest.skipUnless(importlib.util.find_spec("qdrant_client"), "install providers extra")
class QdrantTests(unittest.TestCase):
    def test_local_qdrant_scope_and_upsert(self):
        from agentic_sdk.adapters.qdrant import QdrantStore
        from qdrant_client import QdrantClient

        client = QdrantClient(":memory:")
        try:
            embedder = HashEmbedder()
            store = QdrantStore(client, embedder.profile)
            ctx = Context(
                "one",
                "first",
                frozenset({"index:admin", "knowledge:read", "knowledge:write"}),
            )
            other = replace(ctx, agent_id="second")
            store.provision(ctx)
            store.provision(other)
            store.upsert(ctx, Document("guide", "SDK adapters"), embedder.embed("SDK adapters"))
            store.upsert(ctx, Document("guide", "SDK adapters"), embedder.embed("SDK adapters"))
            self.assertEqual(len(store.search(ctx, embedder.embed("SDK"), 3)), 1)
            self.assertEqual(store.search(other, embedder.embed("SDK"), 3), [])
            with self.assertRaises(PermissionError):
                store.search(replace(ctx, permissions=frozenset()), embedder.embed("SDK"), 3)
        finally:
            client.close()


@unittest.skipUnless(importlib.util.find_spec("opentelemetry"), "install telemetry extra")
class TelemetryTests(unittest.TestCase):
    def test_span_export_contains_no_content(self):
        from agentic_sdk.adapters.otel import OTelTelemetry
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
            InMemorySpanExporter,
        )

        provider = TracerProvider()
        exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        # Avoid global provider state in the test process.
        adapter = OTelTelemetry()
        adapter.tracer = provider.get_tracer("test")
        adapter.record(
            Context("tenant", "agent", frozenset()),
            "agent.request",
            {"status": "ok", "duration_ms": 1.0, "prompt": "secret"},
        )
        spans = exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].attributes["agent_id"], "agent")
        self.assertNotIn("prompt", spans[0].attributes)
        provider.shutdown()

    def test_run_events_share_one_trace_without_content(self):
        from agentic_sdk.adapters.observability.events import PlatformObserver
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
            InMemorySpanExporter,
        )

        provider = TracerProvider()
        exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        observer = PlatformObserver("insight-agent")
        observer.tracer = provider.get_tracer("test")
        ctx = Context("tenant", "agent", frozenset())
        observer.emit(ctx, "run-1", "run.started", {"question": "secret"})
        observer.emit(
            ctx,
            "run-1",
            "tool.completed",
            {"tool": "query_metrics", "duration_ms": 1.5, "result": "secret"},
        )
        observer.emit(
            ctx,
            "run-1",
            "run.finished",
            {"status": "ok", "duration_ms": 2.0, "answer": "secret"},
        )
        spans = {span.name: span for span in exporter.get_finished_spans()}
        parent = spans["agent.run"]
        self.assertEqual(spans["query_metrics"].parent.span_id, parent.context.span_id)
        self.assertEqual(spans["run.finished"].parent.span_id, parent.context.span_id)
        self.assertEqual(spans["query_metrics"].attributes["tool"], "query_metrics")
        self.assertEqual(parent.attributes["status"], "ok")
        for span in spans.values():
            self.assertNotIn("question", span.attributes)
            self.assertNotIn("answer", span.attributes)
            self.assertNotIn("result", span.attributes)
        provider.shutdown()
