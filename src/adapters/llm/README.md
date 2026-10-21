# Language model adapters

## Purpose

Model implementations translate a vendor API into Completion or DecisionModel without vendor types leaking into core.

## Current status

Compatible chat adapter implemented; see provider subfolders.

## Where to work

[Canonical implementation or design](openai_compatible/completion.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) Â· [Reading order](../../../00-START-HERE.md)


## Provider reading order

1. [Azure OpenAI](azure_openai/README.md)
2. [Anthropic — planned](anthropic/README.md)
3. [OpenAI-compatible](openai_compatible/README.md)


## Folder contents

Generation-provider implementations grouped by API family.

- [anthropic/](anthropic/README.md): Native Messages API mapping.
- [azure_openai/](azure_openai/README.md): Azure v1 configuration guide using the shared compatible implementation.
- [openai_compatible/](openai_compatible/README.md): Approved client construction and chat completion mapping.
- [resilient.py](resilient.py): Retry, one fallback provider, a circuit breaker, and structured JSON extract.
