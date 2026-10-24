"""Customer support sequence.

Purpose: the agent order for a refund or an order-status question. Support runs, then billing.
Used by: orchestrator/router/router.py. Phrases that select this name stay in the router.
"""

AGENTS = ["support-agent", "billing-agent"]
