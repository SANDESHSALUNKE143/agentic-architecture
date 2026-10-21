"""
Memory for the insight agent.

The notebook. Owns the instruction and the evidence this agent must
remember before it answers. The tool results of the current question stay
in the harness and are passed back into the foundation model. This module
does not store a chat history.

Usage:
    from insight_agent.memory import INSTRUCTION, REQUIRED_BEFORE_FINAL
"""

# ── Instruction ───────────────────────────────────────────────────────

INSTRUCTION = (
    "Answer from SQL metrics, past analyses, the city graph, the trend model "
    "and the allowlisted public site. Do not invent figures."
)
REQUIRED_BEFORE_FINAL = frozenset({"query_metrics", "search_analyses"})
