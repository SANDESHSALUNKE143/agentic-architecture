# Agent developer guide

The [enterprise guide](guide.md) is the standard. This chapter is how you create, configure, and host an agent after you have copied [insight](../examples/insight_agent/README.md).

## 1. Choose ownership

The platform owns contracts, execution, limits, provider transport, service routes, persistence and telemetry. Your repository owns domain instructions, tool schemas/handlers, model selection, trusted identity mapping and domain evaluations. Never copy `src/`. Pin one tested SDK release and upgrade it with regression evaluations.

## 2. Create and install a runnable agent

Install SDK 0.3.0 from a locally built wheel or approved registry. During development use `python -m pip install -e '/path/to/agentic-architecture[service]'`. Public PyPI publication is not assumed.

```sh
python -m agentic_sdk.developer init ../my-agent --name my-agent
python -m pip install -e ../my-agent
python -m agentic_sdk.developer validate ../my-agent
python -m agentic_sdk.developer run ../my-agent "Is it ready?"
python -m agentic_sdk.developer evaluate ../my-agent ../my-agent/tests/evaluations/readiness.json
```

The generated project is runnable, not an empty scaffold. Its synthetic get_status tool demonstrates the composition seam. `agent.yaml` is JSON syntax compatible with YAML 1.2; this release intentionally parses JSON only. It declares identity, SDK version, installed entrypoint, tools and required evidence. `instructions/system.md` is read by the shared developer runtime and becomes the actual system instruction. `config/local.json` supplies ProjectConfig. The CLI never imports the entrypoint during validation; run/serve/evaluate execute trusted installed project code.

## 3. Add a domain capability

Define an async handler `(Context, dict) -> dict`, register it as ToolSpec with a JSON input schema and a permission string, and give Context only the grants it needs. Use SDK JsonTransport for fixed relative HTTPS endpoints and an environment/secret-provider token callback. Never allow model arguments to choose credentials or arbitrary URLs. Register the tool in manifest capabilities and add required_before_final where evidence is mandatory. Mark side-effecting tools read_only=False; this baseline does not expose model-controlled approvals.

Keep outputs bounded and JSON serializable. Treat backend text as untrusted data. Implement backend authorization independently of model instructions. Tests should prove denied access causes no external operation and required evidence is obtained before answers.

## 4. Select models and knowledge

ProjectConfig's compatible adapter supports approved Azure/OpenAI-compatible endpoints through the provider port. Configure an approved endpoint/model and api_key_env, never the key value. Demo mode is deterministic. To use hosted decisions, compose HostedDecisionModel with the platform transport instead of copying a model loop. [Insight](../examples/insight_agent/README.md) is the reference agent in this repository.

Knowledge endpoints enqueue bounded document chunks. A worker embeds and upserts them into a tenant/agent/profile-specific Qdrant collection. POST /v1/knowledge/documents returns a job; poll GET /v1/knowledge/jobs/{id}; POST /v1/knowledge/search retrieves only that credential's scope. Each content version gets a separate point ID; resubmitting identical content is idempotent. This baseline does not crawl arbitrary websites or parse office files. Delete/ACL-change workflows and content lifecycle management require further implementation before sensitive production ingestion.

## 5. Host the agent

Set AGENT_API_TOKEN to a securely generated secret of at least 32 characters, then:

```sh
python -m agentic_sdk.developer serve ../my-agent
```

Default binding is loopback port 8010. The SDK exposes health plus authenticated run/config/events routes. Pass authorization headers; do not put tokens in URLs. Scope comes from server composition, not request JSON. For containers use the generated Dockerfile with an SDK wheel in vendor and a persistent /state volume. See the [full stack](../deployment/full/README.md) to consume gateways, registry, ingestion and monitoring.

## 6. Register configuration and govern usage

PUT /v1/registry/config accepts expected_revision and config. First revision expects 0; stale writes return 409. GET returns the newest revision or an explicit revision. Rollback means publishing a selected prior configuration as a new revision. Runtime configuration is explicit: publishing does not hot-reload running agents. Validate/evaluate, update deployment configuration, then restart. This avoids changing executing runs midway.

The model gateway reserves a conservative byte-derived token estimate in PostgreSQL before calling a model. Reservation is atomic per tenant/agent/day and survives restart. Failed calls are not refunded. Reported usage is recorded separately. This is a token control, not a currency invoice or distributed reservation system spanning external gateways. Set DAILY_TOKEN_LIMIT for local quotas; provider-side budgets are still required for real spending.

## 7. Evaluate and release

The evaluation command executes cases and checks required tools and answer substrings, returning nonzero on failure. These deterministic checks do not measure factual accuracy. Add realistic sanitized domain questions, expected evidence, stale-data/access-denied cases, latency/cost observations and human review for answer quality. AgentN's existing tests check tool ordering, API scope, redacted metadata and mocked REST contracts.

Run SDK and consumer tests before publishing a wheel/image. Pin dependency resolutions, scan images, rotate test credentials and perform live provider/identity validation before production. [Current verification](verification.md) states what has actually run; [release gaps](release-gates.md) lists remaining boundaries.


## Additional integration adapters

Native Anthropic: configure model as `{"adapter":"anthropic","model":"YOUR_APPROVED_MODEL","api_key_env":"ANTHROPIC_API_KEY"}`. The SDK maps Messages API content and usage into the same Completion/decision ports; no live credential is bundled.

REST/n8n: use adapters.integrations.rest_tool or n8n_tool with a trusted JsonTransport and fixed path. n8n POSTs are mutations and require approved_mutations from trusted application code; the model cannot grant approval. Configure a production webhook with bearer/header authentication and an object JSON response. No transparent retries are performed.

MCP: establish an authenticated ClientSession using your selected MCP SDK transport, initialize it, then wrap explicitly approved names and schemas with adapters.integrations.mcp_tool. Keep the session alive for the runner lifetime. The adapter does not automatically trust tool discovery, launch arbitrary commands, exchange OAuth tokens or share one user's session with another. It supports the MCP v1 Python ClientSession result fields isError and structuredContent; newer MCP major versions need contract validation. See the [official MCP SDK](https://github.com/modelcontextprotocol/python-sdk). Contract tests use fake sessions; network/session lifecycle certification remains your integration responsibility.
