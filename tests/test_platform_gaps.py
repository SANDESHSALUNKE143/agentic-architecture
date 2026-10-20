"""Shared platform gaps: admission, usage, retry, credentials, health, jobs, retrieval, checks."""

import unittest

from agentic_sdk.adapters.llm.resilient import ResilientLLM
from agentic_sdk.adapters.local import HashEmbedder, MemoryStore
from agentic_sdk.adapters.observability.audit import AuditLog
from agentic_sdk.adapters.observability.usage import UsageLog
from agentic_sdk.adapters.retrieval.policy import (
    GovernedStore,
    RetrievalCache,
    query_hash,
    rank_hits,
)
from agentic_sdk.contracts import Completion, Context, Document
from agentic_sdk.contracts.orchestration.types import ExecutionError
from agentic_sdk.core.context.credentials import CredentialStore
from agentic_sdk.core.harness.checks import check_workflow
from agentic_sdk.core.harness.jobs import JobRunner
from agentic_sdk.core.policies.admission import RequestGate, assert_secret_strength
from agentic_sdk.core.policies.health import HealthBoard


class _Result:
    def __init__(self, tools, answer):
        self.tools_used = tools
        self.answer = answer


class _Port:
    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    def complete(self, prompt, max_tokens):
        self.calls += 1
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


class PlatformGapTests(unittest.TestCase):
    def setUp(self):
        self.ctx = Context(
            "tenant",
            "agent",
            frozenset({"agent:invoke", "knowledge:read", "knowledge:write"}),
        )

    def test_rate_body_and_quota(self):
        gate = RequestGate(per_minute=1, max_body_bytes=8, daily_tokens=3, monthly_tokens=5)
        gate.admit(self.ctx, "ok")
        with self.assertRaises(ExecutionError):
            gate.admit(self.ctx, "ok")
        wide = RequestGate(max_body_bytes=4)
        with self.assertRaises(ExecutionError):
            wide.admit(self.ctx, "too-long")
        quota = RequestGate(daily_tokens=2)
        quota.charge(self.ctx, 2)
        with self.assertRaises(ExecutionError):
            quota.admit(self.ctx, "ok")
        assert_secret_strength("api", "x" * 32)
        with self.assertRaises(ValueError):
            assert_secret_strength("api", "password")

    def test_usage_and_resilient_completion(self):
        log = UsageLog()
        primary = _Port([TimeoutError("down"), Completion('{"city":"Pune"}', 3, 2)])
        fallback = _Port([Completion("backup", 1, 1)])
        model = ResilientLLM(
            primary,
            fallback,
            attempts=2,
            usage=log,
            provider="primary",
            model="demo",
            context=self.ctx,
            failures_before_open=5,
        )
        body = model.extract_structured("city?", ("city",))
        self.assertEqual(body["city"], "Pune")
        self.assertEqual(log.summary(self.ctx)["calls"], 1)
        blocked = ResilientLLM(_Port([TimeoutError("down")]), attempts=1, failures_before_open=1)
        with self.assertRaises(ExecutionError):
            blocked.complete("x", 8)
        with self.assertRaises(ExecutionError):
            blocked.complete("x", 8)
        saved = ResilientLLM(_Port([TimeoutError("down")]), fallback, attempts=1)
        self.assertEqual(saved.complete("x", 8).text, "backup")

    def test_credentials_health_and_audit(self):
        store = CredentialStore()
        secret = store.issue(self.ctx, frozenset({"agent:invoke"}))
        self.assertTrue(store.allows(secret, "agent:invoke"))
        store.revoke(secret)
        self.assertIsNone(store.resolve(secret))
        board = HealthBoard()
        board.set("postgres", ok=True)
        board.set("traces", ok=False, detail="unreachable")
        self.assertEqual(board.public()["status"], "degraded")
        with self.assertRaises(ValueError):
            board.set("db", ok=False, detail="postgres://user:password@db")
        audit = AuditLog()
        audit.record(self.ctx, "credential.revoke", "cred-1", "ok")
        with self.assertRaises(ValueError):
            audit.record(self.ctx, "save", "question text", "ok")

    def test_jobs_follow_the_leader(self):
        ran = []
        jobs = JobRunner()
        jobs.register("refresh", 100, lambda: ran.append("refresh"))
        self.assertEqual(jobs.run_due(now=10), ["refresh"])
        self.assertEqual(jobs.run_due(now=20), [])

        class Closed:
            def acquire(self):
                return False

            def release(self):
                raise AssertionError("release is not called when acquire fails")

        quiet = JobRunner(Closed())
        quiet.register("refresh", 1, lambda: ran.append("nope"))
        self.assertEqual(quiet.run_due(now=30), [])
        self.assertEqual(ran, ["refresh"])

    def test_retrieval_policy_and_workflow_check(self):
        embedder = HashEmbedder()
        store = GovernedStore(MemoryStore(embedder.profile))
        document = Document("note-1", "Pune demand rose")
        vector = embedder.embed(document.text)
        store.upsert(self.ctx, document, vector)
        self.assertEqual(store.search(self.ctx, vector, 5)[0].document.id, "note-1")
        store.restrict(self.ctx, "note-1")
        self.assertEqual(store.search(self.ctx, vector, 5), [])
        cache = RetrievalCache()
        key = cache.key(self.ctx, embedder.profile.fingerprint, query_hash("pune"))
        cache.put(key, ["hit"])
        self.assertEqual(cache.get(key), ["hit"])
        ranked = rank_hits(
            [type("H", (), {"score": 0.2})(), type("H", (), {"score": 0.9})()],
            lambda hit: hit.score,
        )
        self.assertEqual(ranked[0].score, 0.9)
        report = check_workflow(
            _Result(["query_metrics"], '{"city":"Pune"}'),
            required_tools=frozenset({"query_metrics"}),
            required_fields=("city",),
        )
        self.assertTrue(report["ok"])
        missed = check_workflow(_Result([], "prose"), required_fields=("city",))
        self.assertEqual(missed["missing_fields"], ["city"])


class RunnerGateTests(unittest.IsolatedAsyncioTestCase):
    async def test_runner_rejects_the_next_request_in_the_same_minute(self):
        from agentic_sdk.execution import AgentRunner, ModelReply, ToolRegistry

        class Final:
            async def decide(self, *args):
                return ModelReply({"type": "final", "answer": "ok"}, 2, 3)

        ctx = Context("tenant", "agent", frozenset({"agent:invoke"}))
        runner = AgentRunner(Final(), ToolRegistry(), "answer", gate=RequestGate(per_minute=1))
        result = await runner.run(ctx, "hello")
        self.assertEqual(result.answer, "ok")
        with self.assertRaises(ExecutionError):
            await runner.run(ctx, "hello")


if __name__ == "__main__":
    unittest.main()
