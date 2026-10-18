> **Source layout updated:** The architecture folders now contain the real Python implementation. See [the source map](docs/source-layout.md). `src/agentic_sdk` retains compatibility entrypoints.

# Start here — platform reading order

```text
agentic-architecture/
  00-START-HERE.md
  contracts/          # 01: models, embeddings, retrieval, orchestration, telemetry, tools
  core/               # 02: harness, context, execution, policies
  adapters/           # 03: llm, embeddings, retrieval, orchestration, observability, persistence
  services/           # 04: model_gateway, tool_gateway, knowledge_service, agent_registry
  sdk/python/         # 05: executable SDK composition and developer commands
  tests/              # 06: contract, integration, compatibility guides + runnable tests
  deployment/         # 07: deployment sequence
  developer-standards/# 08: gcpl-agent-developer skill
  examples/           # 09: runnable reference paths
  src/agentic_sdk/    # stable compatibility imports
```


Keep the requested folder names. Follow the sequence below; filesystem alphabetical ordering is not the architectural dependency order.

| Order | Folder | What you learn |
|---|---|---|
| 01 | [contracts](contracts/README.md) | Provider-neutral interfaces and compatibility rules. Start here before changing implementations. |
| 02 | [core](core/README.md) | The central harness and execution policies reused by every consumer agent. |
| 03 | [adapters](adapters/README.md) | Translate external systems into stable SDK interfaces. Keep vendor details out of core. |
| 04 | [services](services/README.md) | Deployment boundaries for shared platform capabilities; a directory does not imply a deployed service. |
| 05 | [sdk](sdk/README.md) | The versioned installable Python distribution that agents import. |
| 06 | [tests](tests/README.md) | Behavioral evidence for contracts, integrations and backward compatibility. |
| 07 | [deployment](deployment/README.md) | Prototype resource budgets, container entrypoints and future Kubernetes migration. |
| 08 | [developer-standards](developer-standards/README.md) | Rules for adding agents, providers and contracts without copying the harness. |
| 09 | [examples](examples/README.md) | Choose the original local RAG demonstration or the independent Agent N consumer. |

## Code and navigation

The requested top-level folders now contain the real executable implementation. Package-directory mappings install them under agentic_sdk. Existing public imports continue through compatibility re-exports in src/agentic_sdk. See docs/source-layout.md for the file-by-file map; config, schemas, docs and deploy remain supporting assets.

## Independent consumer

The new Agent N consumer lives in its own repository and imports `agentic-foundation-sdk==0.3.0`. Its reading order is manifest → instructions → capabilities → domain → tests → deployment. The original Agent N application repositories are unchanged.

## Developer skill

Use [gcpl-agent-developer](developer-standards/gcpl-agent-developer/SKILL.md) after reading contracts and core. It is engineering guidance and validation tooling, not executable agent policy or a credential store.

## Run and develop

Use the [full local platform](deployment/full/README.md), [agent developer guide](docs/developer-guide.md), and [verified implementation map](docs/implementation-map.md). SDK 0.3.0 adds runnable gateways, registry, ingestion and monitoring; architecture folder READMEs link to the canonical implementation.

## Complete folder inventory

See the [reviewed folder index](docs/folder-index.md) for every maintained directory and its responsibility. Run `python scripts/check_repository.py` to check folder guides, public API docstrings, local links and package mappings.
