"""Order sequence.

Purpose: the agent order for a purchase. The order agent runs, then billing. The write can pause.
Used by: agentic/03-workflows/router/router.py. Phrases that select this name stay in the router.
"""

AGENTS = ["order-agent", "billing-agent"]
