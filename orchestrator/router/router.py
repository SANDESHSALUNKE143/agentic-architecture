"""Pick one specialist or one workflow.

Purpose: an agents list wins, then a workflow name, then the phrases in RULES. The agent order is loaded from workflows/<name>/workflow.py.
Used by: orchestrator/platform.py. Edit phrases here. Edit the order in the workflow file.
"""

from __future__ import annotations

from shared.config import ROOT
from shared.loader import load_module


def _agents(name: str) -> list[str]:
    module = load_module(
        ROOT / "workflows" / name / "workflow.py",
        f"workflow_{name.replace('-', '_')}",
    )
    return list(module.AGENTS)


WORKFLOWS = {
    "product-discovery": _agents("product-discovery"),
    "customer-support": _agents("customer-support"),
    "order-processing": _agents("order-processing"),
}

RULES = [
    ("data-analysis", ("dataset", "sales csv", "mean amount", "analyze")),
    ("research", ("document", "source", "indexed", "according to the")),
    ("customer-support", ("refund", "return", "order status", "order 1001", "order 1002")),
    ("order-processing", ("place an order", "prepare an order", "checkout", "buy ")),
    ("billing", ("discount", "coupon")),
    ("product-discovery", ("jacket", "boot", "lamp", "stock", "shop", "product")),
]

SPECIALISTS = {
    "billing": ["billing-agent"],
    "data-analysis": ["data-analysis-agent"],
    "research": ["research-agent"],
}


def route(task: str, workflow: str | None, agents: list[str] | None) -> tuple[str, list[str]]:
    if agents:
        return "agent-chain", list(agents)
    if workflow:
        if workflow not in WORKFLOWS and workflow not in SPECIALISTS:
            return "unknown", []
        return workflow, list(WORKFLOWS.get(workflow) or SPECIALISTS[workflow])
    lowered = task.lower()
    for name, phrases in RULES:
        if any(phrase in lowered for phrase in phrases):
            if name in SPECIALISTS:
                return name, list(SPECIALISTS[name])
            return name, list(WORKFLOWS[name])
    return "ambiguous", []
