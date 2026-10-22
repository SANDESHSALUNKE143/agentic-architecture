"""Pick a workflow or an agent list. Unknown ids are rejected. Keywords are the mock router."""

from __future__ import annotations

from typing import Any

NAMED = {
    "product-discovery": ["shopping-agent", "catalog-agent", "inventory-agent"],
    "customer-support": ["customer-service-agent", "support-agent", "billing-agent"],
    "order-processing": ["order-agent", "billing-agent"],
    "field-response": [
        "coordinator-agent",
        "satellite-agent",
        "social-media-agent",
        "simulation-agent",
        "logistics-agent",
    ],
}

# First matching rule wins. More specific phrases stay above the general ones.
RULES: list[tuple[tuple[str, ...], str | None, list[str] | None]] = [
    (("refund",), "customer-support", None),
    (("status of order", "order status"), "customer-support", None),
    (("prepare an order", "place an order", "checkout"), "order-processing", None),
    (("compare price", "compare prices"), None, ["personal-shopping-agent"]),
    (("onboard", "new hire"), None, ["enterprise-admin-agent"]),
    (("propose a fix", "apply the patch", "add function"), None, ["software-agent"]),
    (("campaign", "marketing"), None, ["marketing-agent"]),
    (("purchase order", "supplier"), None, ["supplier-agent"]),
    (("soil", "irrigation", "sensor"), None, ["agriculture-agent"]),
    (("hydrat", "health"), None, ["healthcare-agent"]),
    (("imagery", "satellite"), None, ["satellite-agent"]),
    (("approved feed", "social"), None, ["social-media-agent"]),
    (("aftershock", "simulate"), None, ["simulation-agent"]),
    (("dispatch",), None, ["logistics-agent"]),
    (("earthquake", "coordinate a response"), "field-response", None),
    (("dataset", "sales"), None, ["data-analysis-agent"]),
    (("literature", "scientific"), None, ["scientific-research-agent"]),
    (("the source", "document", "quantum", "apparel"), None, ["research-agent"]),
    (("discount",), None, ["billing-agent"]),
    (("available", "in stock", "jacket", "catalog", "product"), "product-discovery", None),
]


def route(
    task: str, request: dict[str, Any], known_agents: set[str], learned: dict | None
) -> dict[str, Any]:
    """Return workflow id, agent ids, and learned_from. error is set when routing fails."""
    if request.get("agents"):
        return {
            "workflow": "agent-chain",
            "agents": list(request["agents"]),
            "learned_from": "",
            "error": None,
        }
    if request.get("workflow"):
        name = request["workflow"]
        if name not in NAMED and name != "agent-chain":
            return _fail("unknown_agent", f"Workflow {name} is not allowlisted.")
        if name == "agent-chain":
            return _fail("schema_invalid", "agent-chain requires an agent list.")
        return {"workflow": name, "agents": list(NAMED[name]), "learned_from": "", "error": None}
    if learned:
        return {
            "workflow": "agent-chain",
            "agents": list(learned["agents"]),
            "learned_from": learned["id"],
            "error": None,
        }
    lowered = task.lower()
    hits = []
    for phrases, workflow, agents in RULES:
        if any(phrase in lowered for phrase in phrases):
            hits.append((workflow, agents))
    if not hits:
        return _fail(
            "ambiguous_intent",
            "The request does not match one workflow. Name a workflow or an agent list.",
        )
    workflow, agents = hits[0]
    if workflow:
        return {
            "workflow": workflow,
            "agents": list(NAMED[workflow]),
            "learned_from": "",
            "error": None,
        }
    unknown = [agent_id for agent_id in agents or [] if agent_id not in known_agents]
    if unknown:
        return _fail("unknown_agent", f"Unknown agent {unknown[0]}.")
    return {"workflow": None, "agents": list(agents or []), "learned_from": "", "error": None}


def _fail(code: str, message: str) -> dict[str, Any]:
    return {
        "workflow": None,
        "agents": [],
        "learned_from": "",
        "error": {"error_code": code, "message": message},
    }
