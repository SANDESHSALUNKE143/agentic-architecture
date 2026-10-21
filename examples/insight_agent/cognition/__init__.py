"""
Cognition for the insight agent.

The foundation model, the planner, and the instruction. The reason loop
that calls them stays in the SDK harness.

- brain.py chooses the next reply.
- planning.py orders the evidence steps.
- memory.py holds the instruction and the required evidence.
"""
