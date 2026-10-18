# Local Docker with AgentN

This is the primary local acceptance path before Ubuntu deployment. Docker Desktop must run Linux containers, with Docker Compose 2.17+ (additional build contexts). Internet access is needed to pull base images and Python dependencies during the build. Runtime demo calls no paid model or private backend.

From the platform checkout in PowerShell:

```powershell
./scripts/local-agentn.ps1 -Action start -AgentNSource 'D:/Projects/AgentN/agent-n-assistant'
./scripts/local-agentn.ps1 -Action test -AgentNSource 'D:/Projects/AgentN/agent-n-assistant'
./scripts/local-agentn.ps1 -Action stop -AgentNSource 'D:/Projects/AgentN/agent-n-assistant'
```

Start builds a fresh SDK wheel from this checkout, installs it in the consumer image, starts the API, and tests health, rejected anonymous access, catalog/status execution, and metadata persistence after restart. Run start/test in the same PowerShell session so the generated token remains available. Stop preserves the named data volume. The test intentionally restarts this prototype service; do not run against a shared production service. A lost token can be replaced by rerunning start; it recreates the binding without deleting history.

The service stays at http://127.0.0.1:8010/docs. Send `Authorization: Bearer <AGENT_API_TOKEN>` to authenticated endpoints. Rebuild with start after SDK or consumer changes. A pre-existing service on port 8010 must be stopped first. No manually copied vendor wheel is used on this path.

On Linux, set AGENTN_SOURCE to the absolute consumer checkout path and AGENT_API_TOKEN to a securely generated token, then run `docker compose -f deployment/local/compose.yaml up -d --build --wait`. The same image runs as UID 65532 with read-only root, a persistent /state volume, 1 CPU and 1 GiB ceiling. These are prototype limits, not measured production sizing. Dependency ranges and the base tag are not a release lockfile; lock and scan them before release.

## Connect the actual backend and model

The verified default is synthetic readiness. To use existing AgentN data, follow the consumer README: create ignored config/agentn-local.json from the Azure example; provide MODEL_API_KEY and AGENTN_ACCESS_TOKEN securely; set AGENT_CONFIG, AGENTN_BACKEND=rest and AGENTN_BASE_URL in a private Compose override. Mount the local config read-only at /app/config/agentn-local.json. Do not commit that override, credentials or private endpoints. Use an approved HTTPS backend reachable from Docker; localhost inside a container is the container itself. Backend user/advertiser grants remain authoritative. Live model/backend validation requires valid credentials and is separate from the local demo acceptance test.

The existing AgentN frontend, backend and MCP repositories are unchanged. This independent agent consumes the SDK and can be called through its HTTP API. Frontend routing, multi-user identity delegation and streaming are future integration work.
