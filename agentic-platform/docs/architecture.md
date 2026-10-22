# Architecture

Read [developer-guide.md](developer-guide.md) for the example index.

```text
dashboard or webhook
  -> apps/agent-api
  -> orchestrator/router
  -> orchestrator/planner
  -> shared/security delegation check
  -> orchestrator/workflow-engine
  -> agents/<name>/agent.py
  -> mcp/tool-gateway
  -> shared/observability trace
  -> orchestrator/state-manager
```

Agents do not import each other. The engine passes a handoff: summary, data, tool calls, and citations.

Short-term memory is the session scratchpad. Long-term memory is an approved note file. Retrieval is a third store: local documents plus a one-hop graph.

Write tools return `needs_approval` and do not run until `POST /approvals/{id}/decision`. The same run id then continues.

The existing SDK stays the tool-permission implementation (`ToolRegistry`) and the n8n webhook adapter. This tree is the product surface on top of it.
