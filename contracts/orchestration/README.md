# Orchestration contracts

## Purpose

DecisionModel, ModelReply, ToolSpec, RunLimits and RunResult isolate consumers from a particular framework.

## Current status

Implemented async decision/tool protocol.

## Where to work

[Canonical implementation or design](../../core/harness/runner.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Async model decisions, run results and observation port.

- [types.py](types.py): Async decision/result contracts and run-event observer interfaces.
