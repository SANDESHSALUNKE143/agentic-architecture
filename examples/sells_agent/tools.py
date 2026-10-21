"""
Tools for the sells agent.

Two hands: read one order, then read its shipping offer.

Usage:
    tools = register(ports)
"""

from agentic_sdk.core.execution.tools import ToolRegistry, ToolSpec

# ── Schemas ───────────────────────────────────────────────────────────

_ORDER = {
    "type": "object",
    "properties": {"order_id": {"type": "string", "enum": ["1001"]}},
    "required": ["order_id"],
}

# ── Hands ─────────────────────────────────────────────────────────────


class _Hands:
    """Order and offer handlers bound to the in-memory book."""

    def __init__(self, ports):
        """Keep the open order book."""
        self.ports = ports

    async def get_order(self, ctx, arguments):
        """Return one order record."""
        del ctx
        return self.ports.orders[arguments["order_id"]]

    async def get_offer(self, ctx, arguments):
        """Return the shipping offer for one order."""
        del ctx
        return self.ports.offers[arguments["order_id"]]

    def specs(self):
        """Return the two tool specifications in call order."""
        return (
            ToolSpec("get_order", "Read one order.", "order:read", _ORDER, self.get_order),
            ToolSpec("get_offer", "Read the shipping offer.", "offer:read", _ORDER, self.get_offer),
        )


def register(ports):
    """Add the two allowlisted tools and return the registry."""
    tools = ToolRegistry()
    for spec in _Hands(ports).specs():
        tools.add(spec)
    return tools
