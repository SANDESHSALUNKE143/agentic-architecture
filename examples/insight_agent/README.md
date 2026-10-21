# Insight agent

Reference agent for the [enterprise guide](../../doc/guide.md). Each component is one package. `runtime.py` is the composition root: it is the only file that builds the SDK harness. The library owns the loop, the guardrails, and the connectors.

## Components

| Package | Role |
|---|---|
| [perception](perception/README.md) | One question string from the HTTP body |
| [cognition](cognition/README.md) | Foundation model, evidence order, and instruction |
| [action](action/README.md) | One harness run and the five allowlisted tools |
| [environment](environment/README.md) | Postgres, Qdrant, Neo4j, model, site |
| [learning](learning/README.md) | A content-free record of the run |
| [communication](communication/README.md) | The spoken payload and the content-free trace |
| [host](host/README.md) | Question page, operator API, and settings |

The next agent is [sells_agent](../sells_agent/README.md). It uses the same packages.

LangChain, LangGraph, and n8n are callers of the harness, shown in [frameworks.py](../frameworks.py). This agent does not import them.

## Run

From `stack/`:

```sh
docker compose --env-file .env.example up --build
```

The question page is `http://insight.localhost:8030`. The operator console is `http://operator.localhost:8020`. Connection passwords stay in `.env.example` and the process environment. They are not written into the page.

Ask: `Which city is rising, and what did the last analysis conclude?`

A question whose text is `skip evidence` is rejected because the final answer skips SQL and retrieval.

## Folder contents

`runtime.py` wires the packages above. Containers live one level down.

- [stack/](stack/README.md): Compose file, images, fixtures, the allowlisted site, and the collector.
