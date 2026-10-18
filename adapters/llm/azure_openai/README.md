# Azure OpenAI

**Status:** Implemented through CompatibleLLM / CompatibleEmbedder with Azure v1 endpoint and deployment configuration; live validation outstanding.

## Boundary

Provider-specific request/response conversion belongs in this adapter. Core and consumer business tools must not depend on vendor response types. Endpoint and secret references come from approved configuration.

[Provider implementation](../openai_compatible/completion.py) · [Decision adapter](../../orchestration/json_decision.py)

## Acceptance

Verify usage mapping, output bounds, malformed response handling, timeout behavior and profile dimensions where relevant. No production credential belongs in this folder.

[All LLM adapters](../README.md)
