# Dependency stack

One Compose file for a server with room for Langfuse. It starts the platform from the root Compose file, then Grafana, Prometheus, an OpenTelemetry collector, Loki, Langfuse, MLflow, n8n, Qdrant, Neo4j, and Postgres.

The root `docker compose up` stays the small stack. This file is the one you run on the larger machine. Langfuse is most of the memory: about 8 GB minimum, 16 GB comfortable. Kibana and Elasticsearch are not in this file.

n8n is source-available. Read [its license](https://github.com/n8n-io/n8n/blob/master/LICENSE.md) before you host it. This image is not part of CI.

## Run

From the repository root:

```bash
docker compose -f infrastructure/dependencies/docker-compose.yml --env-file infrastructure/dependencies/.env.example up -d
./infrastructure/dependencies/check.sh
```

`check.sh` proves each login or ready URL. It does not send a question and it does not post a webhook. CI only runs `docker compose config` on this file.

Copy `.env.example` to `.env` in this folder when you change a password. Keep `LAB_PASSWORD` and the matching `GRAFANA_PASSWORD`, `N8N_TOKEN`, `QDRANT_API_KEY`, `NEO4J_PASSWORD`, and `SQL_CONNECTION` on the same value.

## Lab logins

The shared password in `.env.example` is `lab-password`. `PLATFORM_ENV` stays `development`.

| Service | Address | User |
| --- | --- | --- |
| Console | http://127.0.0.1:5173 | Bearer `local-dev-token-not-for-production` |
| Grafana | http://127.0.0.1:3000 | `admin` |
| Prometheus | http://127.0.0.1:9090 | No login |
| Collector | http://127.0.0.1:13133 | No login |
| Loki | http://127.0.0.1:3100 | No login |
| Langfuse | http://127.0.0.1:3003 | `lab@example.test` |
| MLflow | http://127.0.0.1:5000 | `admin` |
| n8n | http://127.0.0.1:5678 | `lab@example.test` |
| Qdrant | http://127.0.0.1:6333 | API key `lab-password` |
| Neo4j | http://127.0.0.1:7474 | `neo4j` |
| Postgres | `127.0.0.1:5432` database `agentic` | `agentic` |

Grafana opens with a Prometheus datasource and a Loki datasource. Prometheus scrapes itself. The API still keeps its trace in the API process. `invoke_n8n` stays simulated. The API environment receives the in-network addresses, so Connectors shows the hosts configured. The console image still holds no password.

Set `LANGFUSE_PUBLIC_URL` to the address operators type in a browser when that address is not `http://localhost:3003`.
