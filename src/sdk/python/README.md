# Python SDK packaging

## Purpose

Install the repository root or a versioned wheel; agentic_sdk imports remain stable.

## Current status

Implemented here: project configuration, developer CLI, remote agent client and hosted-service adapters. These source files install as agentic_sdk.sdk.python; old public import paths remain compatible.

## Where to work

[Canonical implementation or design](../../../pyproject.toml). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../../00-START-HERE.md)


## Folder contents

Developer commands, composition and remote service clients.

- [config.py](config.py): Version-one local RAG configuration; the agent/hosted paths use ProjectConfig v2.
- [developer.py](developer.py): Generate, validate, run, evaluate and serve independent agent projects.
- [hosted_client.py](hosted_client.py): Client adapters for operator-configured hosted platform endpoints.
- [project.py](project.py): Validated agent settings and reusable model composition.
- [remote_agent.py](remote_agent.py): Client for the optional shared agent API; UI and other services reuse it.
