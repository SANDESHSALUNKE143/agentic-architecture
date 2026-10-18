# Observability

Persist/export metadata by trusted tenant and agent scope: run ID, status, duration, tool name and usage. Do not log prompts, SQL bodies, retrieved passages, completions or credentials by default. SQLiteRunStore and the earlier OTel adapter exist, but a full exported agent-observer pipeline is not automatically configured. Grafana folder/filter settings alone cannot enforce backend query isolation. Define retention and test cross-scope denial.

## Review rule

Check the installed platform version and repository implementation map before applying these standards. Future components require implementation and tests, not only configuration.
