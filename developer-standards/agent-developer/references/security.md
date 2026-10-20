# Security

The existing business backend remains authoritative for current grants and advertiser access. Local SDK Context is a cooperative guard. The prototype agent API maps one opaque token to a fixed workload/agent binding; multi-user production requires verified identity and per-user delegation. Fixed approved destinations, TLS, no redirects, response limits and no implicit retries reduce transport risk. Mutation approval comes from trusted code/users, never the model. No secrets belong in manifests, skill files or examples.

## Review rule

Check the installed platform version and repository implementation map before applying these standards. Future components require implementation and tests, not only configuration.
