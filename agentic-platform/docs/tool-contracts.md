# Tool contracts

See [developer-guide.md](developer-guide.md). Every tool result includes `simulated: true` when it is mock data.

| Tool | Permission | Read only | Required arguments |
| --- | --- | --- | --- |
| search_products | catalog:read | yes | query |
| get_product_details | catalog:read | yes | product_id |
| check_stock | inventory:read | yes | product_id |
| compare_prices | catalog:read | yes | product_id |
| get_order_status | order:read | yes | order_id |
| prepare_order | order:write | no | product_id, user_id |
| get_eligible_discounts | billing:read | yes | user_id, product_id |
| request_approval | support:write | no | action, summary |
| search_documents | research:read | yes | query |
| expand_entity | research:read | yes | entity |
| search_literature | research:read | yes | none |
| analyze_dataset | analysis:read | yes | none; `code` is rejected |
| prepare_provisioning | enterprise:write | no | user_name |
| draft_campaign | enterprise:read | yes | none |
| propose_patch | enterprise:read | yes | none |
| apply_patch | enterprise:write | no | none; dry run |
| analyze_imagery | field:read | yes | none |
| search_feed | field:read | yes | none |
| run_simulation | field:read | yes | none |
| prepare_dispatch | field:write | no | none |
| prepare_purchase_order | field:write | no | none |
| read_sensors | field:read | yes | none |
| irrigate | field:write | no | none |
| health_info | field:read | yes | none |

Write tools are not invoked until a human approval supplies the tool name. Schemas are checked by the SDK `ToolRegistry` before the handler runs.

`search_documents` accepts `pattern`: `classic`, `hybrid`, `agentic`, `corrective`, `graph`, or `multi_hop`. The research agent also calls `expand_entity` itself for graph and multi-hop so both hops appear in the trace.

Error codes on the trace: `unknown_agent`, `delegation_denied`, `tool_denied`, `schema_invalid`, `timeout`, `step_limit`, `loop_detected`, `approval_required`, `approval_stale`, `approval_rejected`, `tool_error`, `provider_error`, `not_implemented`, `ambiguous_intent`.
