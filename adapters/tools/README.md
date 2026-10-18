# tools


## Folder contents

Bounded HTTP, explicit MCP-session and n8n webhook integration.

- [http.py](http.py): Reusable async REST transport. Tokens are injected, never inferred from arguments.
- [integrations.py](integrations.py): Explicit adapters for caller-approved REST/n8n routes and MCP sessions.
