# Infrastructure

This folder builds and checks the API image, the console image, and the mock store image. It does not create a cloud account. The root Compose file does not install Grafana or Langfuse. [dependencies](dependencies/README.md) is the Compose file for a server that can carry Langfuse.

## Files

| File | What it is |
| --- | --- |
| `Dockerfile.api` | The `agentic-api` image. It runs `agentic/01-entry/main.py`. |
| `Dockerfile.console` | The `agentic-console` image. Nginx serves the console. |
| `nginx.conf` | Proxies `/health`, `/platform`, `/agent-runs`, `/approvals`, `/plugins`, `/settings`, `/guide`, and `/memory` to the API. |
| `Dockerfile.merchant` | The mock store image. It is not part of the API image. |
| `smoke.sh` | Waits for the console, then checks health, the seven steps, and one catalog run. |
| [dependencies](dependencies/README.md) | Grafana, Prometheus, Langfuse, MLflow, n8n, and the other connector hosts. |

`docker-compose.yml` stays at the repository root because the build context is the whole tree.

```bash
docker compose up -d --build
./infrastructure/smoke.sh
```

The console publishes port 5173, or `CONSOLE_PORT` when that port is taken. The API has no host port. Operators open the console. The console calls the API on the server network.

## What stays one process

Approvals, traces, notes, and evaluation live in the API process. A second API copy would not see an approval waiting in the first. Add a shared store before you run more than one API.

`docker compose` also starts `mocks/merchant` as its own service and sets `MERCHANT_MCP_URL` to `http://merchant:8091/mcp`. That process is a mock of an outside store. It is not copied into the API image. Replace `MERCHANT_MCP_URL` with the merchant you already run. Sample products are in `mocks/merchant/records.json`.

Secrets belong on the API only: `PLATFORM_DEV_TOKEN`, `MODEL_API_KEY`, `MERCHANT_MCP_TOKEN`, `N8N_TOKEN`, and `SQL_CONNECTION`. The console image holds none. `PLATFORM_ENV=production` refuses the sample token.

`PLATFORM_DATA_DIR` is where the API writes `traces.log` and saved connection addresses. In compose that directory is the `agentic-data` volume. The in-memory trace still clears when the process stops.

## Azure

This repository has no Bicep, Terraform, or Azure DevOps pipeline yet. Add those files here when you host it.

The layout that matches the code:

1. Build `infrastructure/Dockerfile.api` and `infrastructure/Dockerfile.console`.
2. Push `agentic-api` and `agentic-console` to Azure Container Registry.
3. Run the API in Azure Container Apps, or App Service, with internal ingress only.
4. Run the console with external ingress. Its proxy target is the private API.
5. Mount a volume for `PLATFORM_DATA_DIR` when the connection file and `traces.log` must survive a restart.
6. Put the API secrets in an Azure DevOps variable group or Key Vault references. Do not put them in the console.

An Azure DevOps pipeline in this folder, named `azure-pipelines.yml` when you add it, is those six steps plus `./infrastructure/smoke.sh` against the console URL. The merchant, Grafana, and Elasticsearch are not pipeline stages unless your team is the one installing those products. This repository only needs their addresses.

## Grafana, Langfuse, and the other hosts

The API writes the trace itself. The worker in `agentic/06-jobs/workers` stores the run id, stage, agent, tool, and status in `traces.log`. The question is not a field. Nothing in this build posts that line to Grafana or Loki.

| System | Where you set the address | What this build does |
| --- | --- | --- |
| Grafana | Connectors, `GRAFANA_URL` and `GRAFANA_PASSWORD` | Saves the address. It does not open Grafana and does not push the trace. |
| OpenTelemetry | `OTEL_EXPORTER_OTLP_ENDPOINT` | Marks the collector configured. The trace stays in this process. |
| Log store | `OBSERVABILITY_LOG_URL` | Marks the store configured. The worker does not POST the trace there yet. |
| n8n, Qdrant, Neo4j, SQL, the model | The matching variable on Connectors | The local stand-in stays until that host exists. |

Leave these out of the root `docker-compose.yml`. A second copy of this API would split the approval list. On a server with about 16 GB of RAM, [dependencies/docker-compose.yml](dependencies/docker-compose.yml) starts Grafana, Prometheus, the collector, Loki, Langfuse, MLflow, n8n, Qdrant, Neo4j, and Postgres beside the platform. Lab logins and the check command are in [dependencies/README.md](dependencies/README.md). Kibana and Elasticsearch stay out so Langfuse can have the memory. The API still does not call n8n, and it still keeps the trace in its own process.
