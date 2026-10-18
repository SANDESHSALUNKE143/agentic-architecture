# Design Patterns

Use hexagonal ports/adapters and dependency injection at a trusted composition root. Register explicit factories and ToolSpec handlers; do not import code from untrusted config. Keep immutable data contracts separate from provider objects. AgentRunner enforces schema, permissions, prerequisites, result bounds and stopping limits. Extend a port with a versioned compatibility change only when an existing port cannot express the need.

## Review rule

Check the installed platform version and repository implementation map before applying these standards. Future components require implementation and tests, not only configuration.
