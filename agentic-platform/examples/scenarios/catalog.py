"""Every example the developer guide and the dashboard can start."""

from __future__ import annotations

EXAMPLES: dict[str, dict] = {
    "product-discovery": {
        "title": "Product discovery",
        "task": "Find a jacket and check whether it is available",
        "workflow": "product-discovery",
        "group": "workflow",
    },
    "customer-support": {
        "title": "Customer support",
        "task": "What is the status of order 1001?",
        "workflow": "customer-support",
        "group": "workflow",
    },
    "order-processing": {
        "title": "Order processing",
        "task": "Prepare an order for p-jacket-blue",
        "workflow": "order-processing",
        "group": "workflow",
    },
    "agent-chain": {
        "title": "Agent chain",
        "task": "Check stock for the jacket",
        "agents": ["catalog-agent", "inventory-agent"],
        "group": "workflow",
    },
    "field-response": {
        "title": "Field response",
        "task": "Coordinate a response to an earthquake south of the river",
        "workflow": "field-response",
        "group": "workflow",
    },
    "short-term-memory": {
        "title": "Short-term memory",
        "task": "Find a jacket and check whether it is available",
        "workflow": "product-discovery",
        "group": "memory",
    },
    "long-term-memory": {
        "title": "Long-term memory",
        "task": "Find a jacket",
        "workflow": "product-discovery",
        "setup": "note",
        "group": "memory",
    },
    "agent-loop": {
        "title": "Agent loop",
        "task": "Find apparel specs",
        "agents": ["research-agent"],
        "context": {"rag_pattern": "agentic"},
        "group": "learning",
    },
    "human-review": {
        "title": "Human in the loop",
        "task": "Prepare an order for p-jacket-blue",
        "workflow": "order-processing",
        "setup": "approve",
        "group": "learning",
    },
    "feedback": {
        "title": "Feedback",
        "task": "Find a jacket and check whether it is available",
        "workflow": "product-discovery",
        "setup": "feedback",
        "group": "learning",
    },
    "self-learning": {
        "title": "Self-learning",
        "task": "Find a jacket",
        "setup": "learn",
        "group": "learning",
    },
    "rag-classic": {
        "title": "Classic RAG",
        "task": "What does the source say about the blue trail jacket?",
        "agents": ["research-agent"],
        "context": {"rag_pattern": "classic"},
        "group": "rag",
    },
    "rag-agentic": {
        "title": "Agentic RAG",
        "task": "Find apparel specs",
        "agents": ["research-agent"],
        "context": {"rag_pattern": "agentic"},
        "group": "rag",
    },
    "rag-graph": {
        "title": "Graph RAG",
        "task": "What color is the jacket?",
        "agents": ["research-agent"],
        "context": {"rag_pattern": "graph"},
        "group": "rag",
    },
    "rag-hybrid": {
        "title": "Hybrid RAG",
        "task": "What does the source say about the blue trail jacket?",
        "agents": ["research-agent"],
        "context": {"rag_pattern": "hybrid"},
        "group": "rag",
    },
    "rag-corrective": {
        "title": "Corrective RAG",
        "task": "quantum ceramics policy",
        "agents": ["research-agent"],
        "context": {"rag_pattern": "corrective"},
        "group": "rag",
    },
    "rag-multi-hop": {
        "title": "Multi-hop RAG",
        "task": "What does the source say about the blue trail jacket?",
        "agents": ["research-agent"],
        "context": {"rag_pattern": "multi_hop"},
        "group": "rag",
    },
    "failed-run": {
        "title": "Failed run",
        "task": "Hand this to billing",
        "agents": ["healthcare-agent", "order-agent"],
        "group": "trace",
    },
    "n8n-chain": {
        "title": "n8n webhook chain",
        "task": "Find a jacket and check whether it is available",
        "setup": "n8n",
        "group": "n8n",
    },
}

AGENT_EXAMPLES = {
    "catalog-agent": "Find a blue trail jacket",
    "shopping-agent": "Find a jacket and check whether it is available",
    "customer-service-agent": "What is the status of order 1001?",
    "support-agent": "What is the status of order 1001?",
    "inventory-agent": "Is p-jacket-blue in stock?",
    "order-agent": "Prepare an order for p-jacket-blue",
    "billing-agent": "What discount applies to p-jacket-blue?",
    "personal-shopping-agent": "Compare prices for p-jacket-blue",
    "data-analysis-agent": "Analyze the sales dataset",
    "research-agent": "What does the source say about the blue trail jacket?",
    "scientific-research-agent": "Find literature about aftershock risk",
    "enterprise-admin-agent": "Onboard a new hire named Ada",
    "software-agent": "Propose a fix for the add function",
    "marketing-agent": "Draft a campaign for trail-club",
    "coordinator-agent": "Coordinate a response to an earthquake south of the river",
    "satellite-agent": "Review imagery south of the river",
    "social-media-agent": "Search the approved feed for road status",
    "simulation-agent": "Simulate aftershock risk",
    "logistics-agent": "Prepare a dispatch to river-south",
    "supplier-agent": "Prepare a purchase order for p-jacket-blue",
    "agriculture-agent": "Check soil moisture and recommend irrigation",
    "healthcare-agent": "Share general information about rest and hydration",
}

for agent_id, task in AGENT_EXAMPLES.items():
    EXAMPLES[f"agent-{agent_id}"] = {
        "title": agent_id,
        "task": task,
        "agents": [agent_id],
        "group": "agent",
        "context": {"rag_pattern": "classic"} if agent_id == "research-agent" else {},
    }


def list_examples() -> list[dict]:
    rows = []
    for example_id, spec in EXAMPLES.items():
        rows.append(
            {
                "id": example_id,
                "title": spec["title"],
                "group": spec["group"],
                "task": spec["task"],
            }
        )
    return rows
