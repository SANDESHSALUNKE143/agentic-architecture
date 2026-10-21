# Sells agent

The second agent. It uses the same seven components as [insight_agent](../insight_agent/README.md) and answers one order question from memory. It does not open Postgres, Qdrant, or Neo4j.

| Package | Role |
|---|---|
| [perception](perception/README.md) | One question string |
| [cognition](cognition/README.md) | Foundation model, tool order, and instruction |
| [action](action/README.md) | One harness run, the order, and the offer |
| [environment](environment/README.md) | The in-memory order book |
| [learning](learning/README.md) | A content-free record of the run |
| [communication](communication/README.md) | The spoken payload and the content-free trace |

Ask: `What is the status of order 1001, and can I add express shipping?`

The answer names order 1001 as open and says express shipping is available.

`runtime.py` is the only file that builds `AgentRunner`, `RequestGate`, and `Context`. This agent has no `host/` and no `stack/` because it answers in this process.

Run one question from the repository root after the examples directory is on `PYTHONPATH`:

```sh
PYTHONPATH=examples python -m sells_agent
```
