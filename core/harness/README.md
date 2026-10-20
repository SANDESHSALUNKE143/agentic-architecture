# Central harness

## Purpose

AgentRunner owns the model/tool cycle, observations and bounded stopping conditions. Consumers compose it; they never copy it.

## Current status

Implemented; resumable conversation checkpoints are planned.

## Where to work

[Canonical implementation or design](runner.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Async model/tool runner and synchronous RAG example use case.

- [rag.py](rag.py): Small synchronous RAG use case; frameworks may call this from any graph node.
- [runner.py](runner.py): Bounded asynchronous model/tool execution with content-free lifecycle events.
- [jobs.py](jobs.py): Leader-locked job registration that runs inline when no queue is configured.
- [checks.py](checks.py): Workflow checks for required tools and structured fields.
