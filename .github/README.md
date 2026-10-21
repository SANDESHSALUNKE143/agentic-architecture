# Agentic Foundation

![The agent keeps the business. The SDK in the middle runs the loop, enforces the rules, and calls SQL, Qdrant, Neo4j, a model, and the web.](../doc/assets/hero-light.svg)

This repository is the guide for people who build, operate, and review agents. Read the [enterprise guide](../doc/guide.md). The reference agent is [insight](../examples/insight_agent/README.md).

```text
src/          SDK source. Import it as agentic_sdk.
examples/     agents
doc/          guides, diagrams, developer standards, and the adapter sketch
deployment/   stacks, settings, schemas, and run scripts
tests/        unit tests and the retrieval check
```

The library is `agentic-foundation-sdk`. An agent imports it. The library owns the loop, the guardrails, the connectors, and the trace. The agent owns the instruction, the screen, and the tools.

```sh
python -m pip install -e '.[runtime,service,dev]'
python -m unittest discover -s tests -v
```

Commits on this repository are made as [SANDESHSALUNKE143](https://github.com/SANDESHSALUNKE143). Push with a personal access token for that account, stored locally. Do not commit the token.

This `.github` directory also holds the [CI workflows](workflows/README.md). Those files configure repository automation. They are not agent runtime code.

MIT licensed. See [contributing](../CONTRIBUTING.md) and the [security policy](../SECURITY.md).
