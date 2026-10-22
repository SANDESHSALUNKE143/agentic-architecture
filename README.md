# Agentic Foundation

![The agent keeps the business. The SDK in the middle runs the loop, enforces the rules, and calls SQL, Qdrant, Neo4j, a model, and the web.](doc/assets/hero-light.svg)

This repository is the guide for people who build, operate, and review agents. Read the [enterprise guide](doc/guide.md). The reference agent is [insight](examples/insight_agent/README.md).

```text
src/          SDK source. Import it as agentic_sdk.
examples/     agents
doc/          guides, diagrams, developer standards, and the adapter sketch
deployment/   stacks, settings, schemas, and run scripts
tests/        unit tests and the retrieval check
```

The library is `agentic-foundation-sdk`. An agent imports it. The library owns the loop, the guardrails, the connectors, and the trace. The agent owns the instruction, the screen, and the tools.

This machine has no `python` on `PATH`. Use the virtualenv interpreter:

```sh
.venv/bin/python -m pip install -e '.[runtime,service,dev]'
.venv/bin/python -m unittest discover -s tests -v
```

## Run the local platform

The mock multi-agent app is in `agentic-platform/`. It does not need an API key, Qdrant, Neo4j, or n8n.

From the repository root, in one terminal:

```sh
.venv/bin/python -m pip install -e '.[runtime,service,dev]'
.venv/bin/python agentic-platform/apps/agent-api/main.py
```

The API listens on [http://127.0.0.1:8090](http://127.0.0.1:8090). `GET /health` returns `{"status":"ok","mode":"mock"}`.

In a second terminal:

```sh
cd agentic-platform/apps/admin-dashboard
npm install
npm run dev
```

The dashboard is [http://127.0.0.1:5173](http://127.0.0.1:5173). The dev token is `local-dev-token-not-for-production`. The Run screen sends it for you.

A task without the UI:

```sh
.venv/bin/python agentic-platform/cli.py run "Find a jacket and check whether it is available"
```

Platform tests:

```sh
cd agentic-platform && ../.venv/bin/python -m unittest discover -s tests -v
```

Setup, examples, and limits are in [agentic-platform/README.md](agentic-platform/README.md) and [agentic-platform/docs/developer-guide.md](agentic-platform/docs/developer-guide.md).

Commits on this repository are made as [SANDESHSALUNKE143](https://github.com/SANDESHSALUNKE143). Push with a personal access token for that account, stored locally. Do not commit the token.

MIT licensed. See [contributing](CONTRIBUTING.md) and the [security policy](SECURITY.md).
