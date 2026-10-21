"""
Environment for the sells agent.

An in-memory order and one shipping offer. This agent does not open a database.

Usage:
    ports = open_environment()
"""

from dataclasses import dataclass

# ── Orders ────────────────────────────────────────────────────────────


@dataclass
class Ports:
    """The order book and the shipping offers this agent may read."""

    orders: dict
    offers: dict


def open_environment() -> Ports:
    """Return the sample order 1001 and its express offer."""
    return Ports(
        orders={"1001": {"order_id": "1001", "status": "open", "city": "Pune"}},
        offers={"1001": {"order_id": "1001", "offer": "Express shipping is available."}},
    )
