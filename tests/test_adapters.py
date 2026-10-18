"""Provider contract tests with fakes; never contact external services."""

import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock

from agentic_sdk.adapters.local import EchoLLM
from agentic_sdk.adapters.providers import CompatibleEmbedder, CompatibleLLM
from agentic_sdk.contracts import EmbeddingProfile


class ProviderTests(unittest.TestCase):
    def test_chat_usage_and_output_cap_mapping(self):
        c = Mock()
        c.chat.completions.create.return_value = NS(
            usage=NS(prompt_tokens=12, completion_tokens=3),
            choices=[NS(message=NS(content="answer"))],
        )
        result = CompatibleLLM(c, "deployment").complete("question", 50)
        self.assertEqual(result.text, "answer")
        self.assertEqual(result.input_tokens, 12)
        self.assertEqual(c.chat.completions.create.call_args.kwargs["max_completion_tokens"], 50)

    def test_missing_usage_rejected(self):
        c = Mock()
        c.chat.completions.create.return_value = NS(usage=None)
        with self.assertRaises(RuntimeError):
            CompatibleLLM(c, "deployment").complete("question", 50)

    def test_embedding_normalization_and_wrong_dimension(self):
        c = Mock()
        c.embeddings.create.return_value = NS(data=[NS(embedding=[3.0, 4.0])])
        adapter = CompatibleEmbedder(c, "embedding", EmbeddingProfile("model", "1", 2))
        self.assertEqual(adapter.embed("text"), [0.6, 0.8])
        c.embeddings.create.return_value = NS(data=[NS(embedding=[1.0])])
        with self.assertRaises(ValueError):
            adapter.embed("text")

    def test_provider_failure_propagates_without_retry(self):
        c = Mock()
        c.chat.completions.create.side_effect = TimeoutError("synthetic timeout")
        with self.assertRaises(TimeoutError):
            CompatibleLLM(c, "deployment").complete("question", 50)
        self.assertEqual(c.chat.completions.create.call_count, 1)

    def test_demo_output_respects_its_byte_cap(self):
        self.assertLessEqual(EchoLLM().complete("é" * 100, 30).output_tokens, 30)


if __name__ == "__main__":
    unittest.main()
