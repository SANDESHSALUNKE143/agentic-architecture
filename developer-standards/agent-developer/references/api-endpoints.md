# API endpoints

Agent host: GET /health; authenticated GET /v1/agents/{id}/config, POST /v1/agents/{id}/runs, GET /v1/agents/{id}/events.

Local platform: GET /health; credential-scoped GET/PUT /v1/registry/config; POST /v1/models/decide; POST /v1/tools/{name}; POST /v1/knowledge/documents; GET /v1/knowledge/jobs/{id}; POST /v1/knowledge/search; GET /v1/cost/usage.

Tenant/agent identity comes from server credential bindings. Registry writes use expected_revision. Publishing config does not hot-reload execution. Use generated OpenAPI for exact schemas. Operator-approved endpoint URLs and environment secret references belong in deployment configuration, not public guides. AgentN backend tokens and MCP OAuth tokens have different audiences.
