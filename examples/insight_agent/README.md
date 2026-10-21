# Insight agent

Reference agent for the [enterprise guide](../../doc/guide.md). This folder is the agent: `brain.py` is the foundation model. The library owns the harness, the guardrails, and the connectors.

## Components

| Component | File | Owns |
|---|---|---|
| Foundation model | [brain.py](brain.py) | The scripted reply |
| Perception | [perception.py](perception.py) | One question string from the HTTP body |
| Planning | [planning.py](planning.py) | The evidence order |
| Memory | [memory.py](memory.py) | The instruction and the required evidence |
| Action | [action.py](action.py) | One harness run |
| Tools | [tools.py](tools.py) | Metrics, analyses, graph, trend model, site |
| Environment | [environment.py](environment.py) | Postgres, Qdrant, Neo4j, model, site |
| Learning | [learning.py](learning.py) | A content-free record of the run |
| Communication | [communication.py](communication.py) | The payload spoken to the caller |
| Host | [host/](host/README.md) | Question page, operator API, settings, traces |

`runtime.py` composes them. The next agent is [sells_agent](../sells_agent/README.md).

## Run

From `stack/`:

```sh
docker compose --env-file .env.example up --build
```

The question page is `http://insight.localhost:8030`. The operator console is `http://operator.localhost:8020`. Connection passwords stay in `.env.example` and the process environment. They are not written into the page.

Ask: `Which city is rising, and what did the last analysis conclude?`

A question whose text is `skip evidence` is rejected because the final answer skips SQL and retrieval.

## Folder contents

The Python modules above are the agent. Containers live one level down.

- [host/](host/README.md): Question page, operator API, settings, and traces.
- [stack/](stack/README.md): Compose file, images, fixtures, the allowlisted site, and the collector.
