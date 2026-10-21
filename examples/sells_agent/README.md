# Sells agent

The second agent. It uses the same seven components as [insight_agent](../insight_agent/README.md) and answers one order question from memory. It does not open Postgres, Qdrant, or Neo4j.

| Component | File |
|---|---|
| Foundation model | [brain.py](brain.py) |
| Perception | [perception.py](perception.py) |
| Planning | [planning.py](planning.py) |
| Memory | [memory.py](memory.py) |
| Action | [action.py](action.py) |
| Tools | [tools.py](tools.py) |
| Environment | [environment.py](environment.py) |
| Learning | [learning.py](learning.py) |
| Communication | [communication.py](communication.py) |

Ask: `What is the status of order 1001, and can I add express shipping?`

The answer names order 1001 as open and says express shipping is available.

`runtime.py` is the only file that builds `AgentRunner`, `RequestGate`, and `Context`. `host/observe.py` keeps the content-free events. This agent has no `stack/` folder because it does not open a container.

Run one question from the repository root after the examples directory is on `PYTHONPATH`:

```sh
PYTHONPATH=examples python -m sells_agent
```
