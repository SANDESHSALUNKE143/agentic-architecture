# Deployment: one server to hybrid services

> Phase-one design reference. For current executable behavior and the separate consuming agent, read [the current implementation map](implementation-map.md). Features described as planned here are not automatically implemented by the new agent API.

Target prototype: Ubuntu Server 22.04 or 24.04 LTS, 8 vCPU, 32 GB RAM, 200 GB SSD, static IP and internal DNS. There is no HA on one physical host. Host-local LLM inference is outside this sizing; use Azure or another remote inference endpoint.

## Compose quickstart

Install a supported Docker Engine and Compose v2 from official packages. From repository root:

```sh
cp .env.example .env
# Edit .env: replace both data-service passwords with random values.
docker compose config --quiet
docker compose run --build --rm demo
docker compose --profile data up -d
docker compose --profile telemetry up -d
docker compose ps
```

Data profiles start PostgreSQL and Qdrant independently of the demo. The collector only accepts OTLP/HTTP and emits basic diagnostic output. The example uses SafeTelemetry, so starting the collector does not automatically send events to it. Network adapters require explicit composition and optional dependencies. Stop with `docker compose --profile data --profile telemetry down`; do not add `-v` unless intentionally deleting persistent data.

All published ports bind loopback. For remote access use an authenticated TLS reverse proxy/VPN and firewall rules; do not change to `0.0.0.0` without implementing access controls. Containers on the Compose network can reach the unencrypted prototype services. Reject empty or sample credentials before enabling data profiles. A missing PostgreSQL password prevents initialization; Qdrant must not be exposed with an empty API key. Existing volumes retain old database credentials/schema: changing environment variables does not migrate them.

Reference tags are intentionally explicit but have not been certified against current vulnerabilities. Review supported patch versions, pull and scan, then pin immutable image digests. Build a lockfile for each deployed Python image. CI Compose syntax checks do not establish runtime health or security.

## Resource planning (starting estimates, benchmark before commitment)

| Component | vCPU budget | RAM budget | Disk budget |
|---|---:|---:|---:|
| OS/Docker/headroom | 1.0 | 6 GB | 25 GB |
| Agent API + future gateway/config | 1.5 | 4 GB | 5 GB |
| Ingestion workers | 1.0 | 3 GB | 15 GB scratch |
| Qdrant | 1.0 | 4 GB | 35 GB |
| PostgreSQL | 0.5 | 2 GB | 20 GB |
| Collector | 0.5 | 0.5 GB | 2 GB |
| Optional n8n | 0.5 | 1.5 GB | 5 GB |
| Optional Grafana/Prometheus/Loki/Tempo | 1.5 | 6 GB | 43 GB |
| Unallocated reserve | 0.5 | 5 GB | 50 GB |
| Total | 8.0 | 32 GB | 200 GB |

The table is a design envelope, not resources automatically provisioned by Compose. Compose implements limits only for demo, PostgreSQL, Qdrant and Collector. Full local telemetry needs measured retention and rate controls; prefer hosted backends if ingestion/query workloads compete. 10,000 documents x 10 chunks x 1,536 dimensions x 4 bytes is about 614 MB of raw vectors; indexes, payloads, replicas, WAL, snapshots and temporary reindexing consume additional capacity. Document count alone is not a sizing input.

Alert at disk 70%, pause bulk ingestion at 80%, emergency response at 90%; reserve space for WAL and compaction. Set Docker log rotation for all new services. Do not store the only backup on the same disk. Define daily PostgreSQL backups + WAL policy and Qdrant snapshots to protected off-host storage; test coordinated restore with the source manifest and profile fingerprint. A restored database with an incompatible vector index must not serve queries.

## Hybrid Azure deployment

Run agent workloads, n8n (optional) and lightweight collector on-prem. Point adapters at approved hosted endpoints: Azure OpenAI/compatible inference, Azure Database for PostgreSQL or self-managed PostgreSQL on Azure VMs, and self-managed Qdrant/observability on Azure infrastructure or separately contracted managed services. Azure hosting does not automatically make every component a managed service or free. Azure Monitor/Grafana offerings have their own capabilities, pricing and networking; they are alternatives to self-hosting, not assumed drop-in deployments in this repo.

Use private routing/VPN, DNS resolution from the server, certificate trust, outbound allowlists and measured round-trip latency. Avoid exposing database ports publicly. Store secrets in a vault; managed identity from an on-prem host requires an appropriate supported federation/identity setup, not an assumed VM identity. Test DNS/credential expiry/outage scenarios. Configuration selects adapters and endpoints, leaving domain code unchanged. Prefer running ingestion near its data store to reduce transfer volume.

## Kubernetes / Helm migration (planned, no chart supplied)

`deployment/earlier/helm/values-draft.yaml` is a capacity/design input only. Build a chart after the services exist: Deployments for stateless APIs/workers, Jobs for migrations/evaluations, external operators/managed services for stateful stores, ConfigMaps for nonsecrets and external secret integration. Provide startup/readiness/liveness probes, PodDisruptionBudgets only with multiple replicas, restricted pod security, dedicated service accounts, network policies, resource quotas and persistent storage classes.

Initial request/limit: agent API 250m/1 CPU and 512Mi/2Gi; ingestion worker 500m/1 CPU and 1Gi/3Gi; collector 100m/500m and 256Mi/512Mi. Scale API on latency/concurrency and workers on queue depth, with provider quota as the upper bound. Use anti-affinity and multiple nodes for HA; installing Kubernetes on the same single host does not add hardware availability. Move state first with backup/restore verification, deploy stateless services, shadow traffic, switch DNS/routes and retain rollback snapshots. Do not deploy two writers against mismatched schema versions.
