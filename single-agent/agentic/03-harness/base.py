"""Shared harness return.

Purpose: every adapter returns tool outcomes already captured by the caller, plus the model reply.
Used by: the three adapters in this folder and agentic/03-harness/runtime.py.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HarnessResult:
    reply: str = ""
    error: str = ""
