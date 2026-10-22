"""Pick one specialist or one of the three workflows."""

from __future__ import annotations

WORKFLOWS = {
    "product-discovery": ["shopping-agent", "catalog-agent", "inventory-agent"],
    "customer-support": ["support-agent", "billing-agent"],
    "order-processing": ["order-agent", "billing-agent"],
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
