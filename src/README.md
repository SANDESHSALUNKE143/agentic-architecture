# SDK source

This folder is the library. Install it and import `agentic_sdk`.

[Examples](../examples/README.md) are the agents. [Documentation](../doc/README.md) is the reading path. [Deployment](../deployment/README.md) is how a stack runs.

| Folder | What it is |
|---|---|
| [contracts](contracts/README.md) | Ports: the shapes every agent shares |
| [core](core/README.md) | Harness, identity, permissions, and policies |
| [adapters](adapters/README.md) | SQL, Qdrant, Neo4j, models, the web, language models, and traces |
| [services](services/README.md) | Operator console and the platform HTTP |
| [sdk](sdk/README.md) | Developer commands and the installable client |
| [agentic_sdk](agentic_sdk/README.md) | Older import names. They point at the folders above. |

The library does not import an agent. An agent imports the library.
