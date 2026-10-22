# Agentic platform

Local multi-agent prototype. It runs without an API key, Qdrant, Neo4j, or a live n8n server.

Request path:

1. `apps/admin-dashboard` or `cli.py` sends a task.
2. `orchestrator/router` picks a workflow or an agent list.
3. `orchestrator/planner` checks the delegation matrix and the hop limit.
4. `orchestrator/workflow-engine` runs one agent, then passes a structured handoff to the next.
5. Agents call tools only through `mcp/tool-gateway`.
6. The trace records every step, including what stopped the run.

Commands below are from the repository root. `python` is not on `PATH` here, so the commands use `.venv/bin/python`.

Terminal 1, API on [http://127.0.0.1:8090](http://127.0.0.1:8090):

```sh
.venv/bin/python -m pip install -e '.[runtime,service,dev]'
.venv/bin/python agentic-platform/apps/agent-api/main.py
```

`GET /health` returns `{"status":"ok","mode":"mock"}`.

Terminal 2, dashboard on [http://127.0.0.1:5173](http://127.0.0.1:5173):

```sh
cd agentic-platform/apps/admin-dashboard
npm install
npm run dev
```

The dev token is `local-dev-token-not-for-production`. The Run screen fills it in. `PLATFORM_ENV=production` rejects that token.

One task from the CLI, with the API left stopped:

```sh
.venv/bin/python agentic-platform/cli.py run "Find a jacket and check whether it is available"
```

Tests:

```sh
cd agentic-platform && ../.venv/bin/python -m unittest discover -s tests -v
```

The developer guide is [docs/developer-guide.md](docs/developer-guide.md).
