# Architecture ownership

The platform owns contracts, execution, policy, provider/transport adapters, telemetry and reusable HTTP routes. Source lives in `src/` and is packaged under agentic_sdk through explicit setuptools mappings. `src/agentic_sdk` provides compatibility imports. Consumers own domain instructions, business tools, composition and evaluations.

The local platform API combines registry, model/tool and knowledge route modules; a separate worker drains PostgreSQL ingestion jobs into Qdrant. AgentN can consume hosted model/tool APIs or use direct SDK composition. Publishing registry configuration does not hot-reload a running agent. Read doc/source-layout.md, doc/implementation-map.md and doc/developer-guide.md in the platform checkout.

Do not couple the SDK to AgentN backend internals or business SQL rules. Static credential bindings are the local identity boundary; production end-user federation and a custom visual portal remain separate work.
