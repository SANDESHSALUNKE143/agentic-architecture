# Provider catalog

SDK 0.3.0 implements deterministic adapters; Azure/OpenAI-compatible chat/embeddings; native Anthropic Messages; Qdrant; content-free OTel export; SQLite run metadata; PostgreSQL platform state; bounded REST; explicitly allowed MCP ClientSession tools; and mutation-gated n8n webhooks.

Only synthetic/local infrastructure is acceptance-tested. Anthropic/MCP/n8n contracts use fakes. MCP transport lifecycle/OAuth must be established by trusted application composition; no automatic tool-discovery trust is implied. Framework wrappers are optional; use the framework-independent harness directly.
