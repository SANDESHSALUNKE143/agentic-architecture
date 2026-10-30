"""Scaffold checks.

Purpose: a new problem becomes a contract, a tool, and a workflow the mock loop can call.
Used by: CI and the local test command.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agentic.platform.loader import load_module  # noqa: E402
from agentic.platform.scaffold import create  # noqa: E402
from loops.llm.mock import tool_arguments  # noqa: E402


class ScaffoldTests(unittest.TestCase):
    def test_a_problem_becomes_a_callable_agent(self):
        with tempfile.TemporaryDirectory() as folder:
            made = create(
                "invoice-review",
                "Look up an invoice and explain what is unpaid",
                Path(folder),
            )
            tool = load_module(Path(folder) / made["tool"], "invoice_review_tools")
            result = tool.lookup_invoice_review("invoice 44")
            self.assertIn("invoice 44", result["answer"])
            self.assertEqual(tool.TOOLS["lookup_invoice_review"]["permission"], "invoice_review_read")
            contract = (Path(folder) / made["agent"]).read_text(encoding="utf-8")
            self.assertIn("Look up an invoice and explain what is unpaid", contract)
            self.assertIn("invoice review", (Path(folder) / made["workflow"]).read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                create("invoice-review", "Look up an invoice and explain what is unpaid", Path(folder))

    def test_mock_fills_arguments_for_a_new_tool(self):
        class _Field:
            annotation = str

        class _Schema:
            model_fields = {"query": _Field()}

        class _Tool:
            args_schema = _Schema()

        args = tool_arguments("lookup_invoice_review", "invoice 44", _Tool())
        self.assertEqual(args["query"], "invoice 44")
        self.assertEqual(tool_arguments("search_products", "jacket")["query"], "jacket")
