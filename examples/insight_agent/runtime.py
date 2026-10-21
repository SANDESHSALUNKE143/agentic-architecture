"""
Compose the insight agent from the component roadmap and the SDK harness.

Perception, cognition, action, the environment, learning, and
communication are the packages beside this file. The reason loop stays
in the library.
build() opens the environment, registers the tools, and returns the runner
the product page and the operator API already call.

Usage:
    runner, context, trace, tools, allowlists, bindings, sql, models, web = build()
"""

import os

from agentic_sdk.contracts import Context
from agentic_sdk.core.harness.runner import AgentRunner
from agentic_sdk.core.policies.admission import RequestGate

from insight_agent.action.tools import register
from insight_agent.cognition.brain import ScriptedModel
from insight_agent.cognition.memory import INSTRUCTION, REQUIRED_BEFORE_FINAL
from insight_agent.communication.observe import Fanout, TraceObserver
from insight_agent.environment import open_environment
from insight_agent.host.settings import Bindings

# ── Composition ───────────────────────────────────────────────────────


def build():
    """
    Connect the SDK adapters and return the runner plus the live bindings.

    Steps:
        1. Open the environment and seed the fixtures.
        2. Register the five tools.
        3. Require query_metrics and search_analyses before a final answer.
    """
    ports = open_environment()
    tools = register(ports)
    trace = TraceObserver()
    sinks = [trace]
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from agentic_sdk.adapters.observability.events import PlatformObserver

        sinks.append(PlatformObserver("insight-agent"))
    bindings = Bindings()
    runner = AgentRunner(
        ScriptedModel(bindings),
        tools,
        INSTRUCTION,
        observer=Fanout(sinks),
        required_before_final=REQUIRED_BEFORE_FINAL,
        gate=RequestGate(),
    )
    context = Context(
        "example-tenant",
        "insight-agent",
        frozenset(
            {
                "agent:invoke",
                "sql:read",
                "knowledge:read",
                "graph:read",
                "model:invoke",
                "web:read",
            }
        ),
    )
    allowlists = {
        "sql_tables": [bindings.sql_table],
        "models": [bindings.model_id],
        "web_hosts": [bindings.web_host],
        "retrieval": bindings.retrieval,
        "graph": bindings.graph,
    }
    return (
        runner,
        context,
        trace,
        tools,
        allowlists,
        bindings,
        ports.sql,
        ports.models,
        ports.web,
    )
