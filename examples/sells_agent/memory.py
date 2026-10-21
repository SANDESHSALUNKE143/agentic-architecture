"""
Memory for the sells agent.

The notebook. The instruction and the evidence required before an answer.

Usage:
    from sells_agent.memory import INSTRUCTION, REQUIRED_BEFORE_FINAL
"""

# ── Instruction ───────────────────────────────────────────────────────

INSTRUCTION = "Answer from the order record and the shipping offer. Do not invent a price."
REQUIRED_BEFORE_FINAL = frozenset({"get_order", "get_offer"})
