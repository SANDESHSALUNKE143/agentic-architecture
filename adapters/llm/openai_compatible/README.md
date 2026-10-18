# OpenAI-compatible endpoints

**Status:** Implemented generic chat and embeddings clients. Model-specific parameter compatibility must be tested per endpoint.

## Boundary

Provider-specific request/response conversion belongs in this adapter. Core and consumer business tools must not depend on vendor response types. Endpoint and secret references come from approved configuration.

[Provider implementation](completion.py) · [Decision adapter](../../orchestration/json_decision.py)

## Acceptance

Verify usage mapping, output bounds, malformed response handling, timeout behavior and profile dimensions where relevant. No production credential belongs in this folder.

[All LLM adapters](../README.md)


## Folder contents

Approved client construction and chat completion mapping.

- [client.py](client.py): Validated compatible-provider client construction and credential resolution.
- [completion.py](completion.py): Chat-completion mapping for Azure v1 and other compatible endpoints.
