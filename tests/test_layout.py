"""The old API and architectural imports must resolve to the same implementation."""

import unittest

from agentic_sdk.contracts import Context
from agentic_sdk.core.context.identity import Context as ArchitecturalContext
from agentic_sdk.core.execution.tools import ToolRegistry as ArchitecturalTools
from agentic_sdk.core.harness.runner import AgentRunner as ArchitecturalRunner
from agentic_sdk.core.policies.limits import RunLimits as ArchitecturalLimits

from agentic_sdk.execution import AgentRunner, RunLimits, ToolRegistry


class LayoutTests(unittest.TestCase):
    def test_compatibility_imports_do_not_duplicate_classes(self):
        self.assertIs(Context, ArchitecturalContext)
        self.assertIs(AgentRunner, ArchitecturalRunner)
        self.assertIs(RunLimits, ArchitecturalLimits)
        self.assertIs(ToolRegistry, ArchitecturalTools)
