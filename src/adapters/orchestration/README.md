# Framework integration adapters

## Purpose

Wrap the SDK runner in a framework node if needed; preserve SDK contracts outside framework-specific state.

## Current status

Direct framework-independent runtime implemented. LangChain and LangGraph call that runtime through the wrappers in this folder. n8n is the webhook tool in adapters/tools.

## Where to work

[Canonical implementation or design](../../core/harness/runner.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../../00-START-HERE.md)


## Folder contents

JSON decision adapter; no required agent framework.

- [json_decision.py](json_decision.py): Decision adapters wrap provider clients without imposing an agent framework.
- [langchain.py](langchain.py): LangChain tool that runs one governed question.
- [langgraph.py](langgraph.py): LangGraph node that runs one governed question.
