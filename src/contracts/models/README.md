# Model contracts

## Purpose

LLM.complete returns Completion with text and token usage; DecisionModel.decide returns a validated tool/final decision.

## Current status

Implemented. Provider-native tool-calling contracts are not yet supplied.

## Where to work

[Canonical implementation or design](../../core/harness/runner.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../../00-START-HERE.md)


## Folder contents

Synchronous model/completion port.

- [types.py](types.py): Synchronous language-model port and provider-neutral completion result.
