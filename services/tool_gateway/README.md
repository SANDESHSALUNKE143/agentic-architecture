# Tool gateway

POST /v1/tools/{name}. Fixed allowlist for AgentN catalog, freshness and SQL; fixed approved backend endpoint/credential. Synthetic mode is default. No model-selected URLs or mutation tools. Reusable MCP session and n8n webhook adapters are available in adapters/integrations.py; this local tool gateway exposes only its AgentN allowlist.

[Implementation](../app.py) - [Local runbook](../../deployment/full/README.md) - [Developer guide](../../docs/developer-guide.md).

Validation: scripts/test_full_platform.py against the running stack. These APIs share one local process; independent service scaling is future work.


## Folder contents

Fixed AgentN tool allowlist and backend forwarding.

- [routes.py](routes.py): Allowlisted AgentN tool API with synthetic or approved backend transport.
