import json
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_sdk.config import load


class ConfigurationTests(unittest.TestCase):
    def test_invalid_config_rejected(self):
        original = json.loads(Path("config/local.json").read_text())
        cases = [
            dict(original, token_budget=True),
            dict(original, llm_adapter="untrusted.module"),
            dict(original, tenant_id="../other"),
            dict(original, schema_version=2),
            dict(original, secret="literal"),
            dict(original, max_output_tokens=0),
        ]
        for case in cases:
            with (
                self.subTest(case=case),
                patch.object(Path, "read_text", return_value=json.dumps(case)),
            ):
                with self.assertRaises(ValueError):
                    load("synthetic-config.json")
