"""Product discovery sequence.

Purpose: the agent order for a product question. Shopping runs, then catalog, then inventory.
Used by: orchestrator/router/router.py. Phrases that select this name stay in the router.
"""

AGENTS = ["shopping-agent", "catalog-agent", "inventory-agent"]
