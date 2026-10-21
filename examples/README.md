# Examples

Each agent is one folder under `examples/`.

- [insight_agent](insight_agent/README.md) is the reference agent. Its containers are in `insight_agent/stack/`.
- [sells_agent](sells_agent/README.md) is the second agent, with the same seven components and an in-memory order.
- [minimal.py](minimal.py) is the smaller local RAG script.
- [frameworks.py](frameworks.py) calls the harness from LangChain, LangGraph, and an n8n webhook.

The library does not import these agents. They import the library.

## Folder contents

- [insight_agent/](insight_agent/README.md): City question, connectors, and the local stack.
- [sells_agent/](sells_agent/README.md): Order question on the same component roadmap.
- [minimal.py](minimal.py): Executable RAG demonstration.
- [frameworks.py](frameworks.py): LangChain tool, LangGraph node, and n8n webhook.
