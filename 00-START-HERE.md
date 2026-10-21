![The agent keeps the business. The SDK in the middle runs the loop, enforces the rules, and calls SQL, Qdrant, Neo4j, a model, and the web.](doc/assets/hero-light.svg)

# Start here

Read the [enterprise guide](doc/guide.md). It is the standard for building, operating, and reviewing an agent. The reference agent is [insight](examples/insight_agent/README.md).

```text
src/          SDK source. Import it as agentic_sdk.
examples/     agents
doc/          guides, diagrams, developer standards, and the adapter sketch
deployment/   stacks, settings, schemas, and run scripts
tests/        unit tests and the retrieval check
```

Inside `src/`, read contracts, then core, then adapters, then services, then the developer client. `src/agentic_sdk` keeps the older import names.

| Order | Folder | What you learn |
|---|---|---|
| 01 | [contracts](src/contracts/README.md) | Provider-neutral interfaces and compatibility rules. Start here before changing implementations. |
| 02 | [core](src/core/README.md) | The central harness and execution policies reused by every consumer agent. |
| 03 | [adapters](src/adapters/README.md) | Translate external systems into stable SDK interfaces. Keep vendor details out of core. |
| 04 | [services](src/services/README.md) | Deployment boundaries for shared platform capabilities; a directory does not imply a deployed service. |
| 05 | [sdk](src/sdk/README.md) | The versioned installable Python distribution that agents import. |
| 06 | [tests](tests/README.md) | Behavioral evidence for contracts, integrations and backward compatibility. |
| 07 | [deployment](deployment/README.md) | Prototype resource budgets, container entrypoints and future Kubernetes migration. |
| 08 | [developer-standards](doc/developer-standards/README.md) | Rules for adding agents, providers and contracts without copying the harness. |
| 09 | [examples](examples/README.md) | The insight reference agent, plus the smaller RAG script. |

## Code and navigation

`src/` is the executable SDK. Package-directory mappings install it as `agentic_sdk`. Older imports stay available through `src/agentic_sdk`. See [source layout](doc/source-layout.md) for the file-by-file map. `examples/` holds the agents. `doc/` holds the guides. Earlier deployment drafts live under `deployment/earlier`.

## Reference agent

[Insight](examples/insight_agent/README.md) lives in this repository and imports `agentic-foundation-sdk`. Copy it when you add the next agent. Keep the seven components: foundation model, perception, planning, memory, action, learning, and communication. Replace the instruction and the tools.

## Developer skill

Use [agent-developer](doc/developer-standards/agent-developer/SKILL.md) after reading contracts and core. It is engineering guidance and validation tooling, not executable agent policy or a credential store.

## Run and develop

Use the [full local platform](deployment/full/README.md), [agent developer guide](doc/developer-guide.md), and [verified implementation map](doc/implementation-map.md). SDK 0.3.0 adds runnable gateways, registry, ingestion and monitoring; architecture folder READMEs link to the canonical implementation.

## Complete folder inventory

See the [reviewed folder index](doc/folder-index.md) for every maintained directory and its responsibility. Run `python deployment/scripts/check_repository.py` to check folder guides, public API docstrings, local links and package mappings.
