"""
Compose the sells agent from the component roadmap and the SDK harness.

The seven components live in the packages beside this file. The reason loop, the request
gate, and the trusted context stay in the library. build() opens the
in-memory book, registers the tools, and returns the runner.

Usage:
    runner, context, trace = build()
"""

import os

from agentic_sdk.contracts import Context
from agentic_sdk.core.harness.runner import AgentRunner
from agentic_sdk.core.policies.admission import RequestGate

from sells_agent.action.tools import register
from sells_agent.cognition.brain import ScriptedModel
from sells_agent.cognition.memory import INSTRUCTION, REQUIRED_BEFORE_FINAL
from sells_agent.communication.observe import Fanout, TraceObserver
from sells_agent.environment import open_environment

# ── Composition ───────────────────────────────────────────────────────


def build():
    """
    Connect the SDK harness and return the runner.

    Steps:
        1. Open the in-memory environment.
        2. Register the order tools.
        3. Require get_order and get_offer before a final answer.
    """
    ports = open_environment()
    tools = register(ports)
    trace = TraceObserver()
    sinks = [trace]
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from agentic_sdk.adapters.observability.events import PlatformObserver

        sinks.append(PlatformObserver("sells-agent"))
    runner = AgentRunner(
        ScriptedModel(),
        tools,
        INSTRUCTION,
        observer=Fanout(sinks),
        required_before_final=REQUIRED_BEFORE_FINAL,
        gate=RequestGate(),
    )
    context = Context(
        "example-tenant",
        "sells-agent",
        frozenset({"agent:invoke", "order:read", "offer:read"}),
    )
    return runner, context, trace
