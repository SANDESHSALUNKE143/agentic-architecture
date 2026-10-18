import json
import tempfile
import unittest
from pathlib import Path

from agentic_sdk.developer import scaffold, validate


class DeveloperTests(unittest.TestCase):
    def test_generated_agent_manifest_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = scaffold(Path(temp) / "agent", "test-agent")
            _, manifest, config = validate(root)
            self.assertEqual(config.agent_id, "test-agent")
            self.assertEqual(manifest["capabilities"], ["get_status"])
            with self.assertRaises(ValueError):
                scaffold(root, "test-agent")

    def test_escape_and_sdk_mismatch_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root = scaffold(Path(temp) / "agent", "test-agent")
            path = root / "agent.yaml"
            original = json.loads(path.read_text())
            for change in (
                {"instruction_reference": "../outside.md"},
                {"sdk": {"distribution": "agentic-foundation-sdk", "version": "999"}},
            ):
                path.write_text(json.dumps({**original, **change}))
                with self.assertRaises(ValueError):
                    validate(root)

    def test_invalid_names_leave_no_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "agent"
            with self.assertRaises(ValueError):
                scaffold(root, "../escape")
            self.assertFalse(root.exists())


class ConfigurationSecurityTests(unittest.TestCase):
    def test_embedded_provider_credentials_rejected(self):
        from agentic_sdk.project import ProjectConfig

        for url in (
            "http://example.invalid",
            "https://user:secret@example.invalid",
            "https://example.invalid?api_key=secret",
        ):
            with self.assertRaises(ValueError):
                ProjectConfig.from_dict(
                    {
                        "schema_version": 2,
                        "tenant_id": "t",
                        "agent_id": "a",
                        "model": {
                            "adapter": "compatible",
                            "base_url": url,
                            "model": "m",
                            "api_key_env": "KEY",
                        },
                        "limits": {},
                    }
                )
