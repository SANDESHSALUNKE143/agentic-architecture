import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from agentic_sdk.adapters.local import EchoLLM, HashEmbedder, MemoryStore, SafeTelemetry
from agentic_sdk.contracts import Context, Document

from agentic_sdk.config import load
from agentic_sdk.registry import Registry
from agentic_sdk.runtime import Agent, Budget


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.e = HashEmbedder()
        self.s = MemoryStore(self.e.profile)
        self.t = SafeTelemetry()
        self.ctx = Context(
            "tenant-a",
            "agent-a",
            frozenset({"knowledge:read", "knowledge:write", "agent:invoke"}),
        )
        self.a = Agent(EchoLLM(), self.e, self.s, self.t, Budget(20000))

    def test_rag_and_idempotent_upsert(self):
        self.a.ingest(self.ctx, Document("1", "shared SDK adapters"))
        self.a.ingest(self.ctx, Document("1", "shared SDK adapters"))
        self.assertEqual(self.a.ask(self.ctx, "SDK").sources, ("1",))

    def test_cross_agent_and_tenant_isolation(self):
        self.a.ingest(self.ctx, Document("secret", "private data"))
        for ctx in [
            replace(self.ctx, agent_id="agent-b"),
            replace(self.ctx, tenant_id="tenant-b"),
        ]:
            self.assertEqual(self.a.ask(ctx, "private").sources, ())

    def test_deny_before_provider_call(self):
        with self.assertRaises(PermissionError):
            self.a.ask(replace(self.ctx, permissions=frozenset()), "SDK")

    def test_same_dimensions_different_model_rejected(self):
        self.s.profile = replace(self.e.profile, model="other-model")
        with self.assertRaises(ValueError):
            Agent(EchoLLM(), self.e, self.s, self.t, Budget(100))

    def test_bad_vectors(self):
        for vector in [[0.0] * 64, [float("nan")] * 64, [1.0]]:
            with self.assertRaises(ValueError):
                self.s.upsert(self.ctx, Document("1", "x"), vector)

    def test_atomic_budget(self):
        budget = Budget(10)

        def spend(_):
            try:
                budget.reserve(1)
                return True
            except RuntimeError:
                return False

        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(spend, range(30))), 10)
        self.assertEqual(budget.remaining, 0)

    def test_budget_blocks_generation(self):
        self.a.budget = Budget(1)
        with self.assertRaises(RuntimeError):
            self.a.ask(self.ctx, "long question")

    def test_telemetry_content_filter(self):
        self.t.record(self.ctx, "test", {"prompt": "secret", "api_key": "secret", "status": "ok"})
        self.assertNotIn("secret", str(self.t.events))

    def test_registry_fail_closed(self):
        r = Registry()
        r.register("echo", EchoLLM)
        with self.assertRaises(ValueError):
            r.register("echo", EchoLLM)
        with self.assertRaises(ValueError):
            r.create("arbitrary.module")

    def test_config(self):
        self.assertEqual(load("config/local.json").agent_id, "demo-agent")


if __name__ == "__main__":
    unittest.main()
