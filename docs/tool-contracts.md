# Tool contracts

Each plugin is a registered tool. An industry system replaces the local stand-in behind the same name, permission, and approval rule. The gateway is the only caller. A tool runs when the agent contract lists it and the permission is true.

| Tool | Permission | Approval |
| --- | --- | --- |
| search_products | catalog_read | no |
| get_product_details | catalog_read | no |
| compare_products | catalog_read | no |
| check_stock | inventory_read | no |
| get_order_status | order_read | no |
| prepare_order | order_write | yes, when the order contract's `amount_gte` is met |
| get_eligible_discounts | billing_read | no |
| request_approval | support_write | yes |
| search_documents | research_read | no |
| analyze_dataset | analysis_read | no |
| query_sql | sql_read | no, and only a SELECT is accepted |
| fetch_url | web_read | no, and the host must be on `WEB_ALLOWLIST` |
| invoke_n8n | n8n_write | yes |
| use_mcp_server | mcp_client | no. Lists the tools on a configured MCP server |

`check_stock`, `search_documents`, and `analyze_dataset` are registered by `agentic/05-tools/mcp/tool-gateway` from `agentic/04-loops/memory`. The sales fixture is `agentic/04-loops/memory/fixtures/sales.csv`.

`get_product_details` calls the MCP server whose purpose is product. The price is not stored in this repository. `examples/merchant-mcp` is a separate process you can run locally; its `records.json` is the merchant's catalog. Orders, discounts, and support requests follow the same pattern with purposes `orders`, `billing`, and `support`.

Open a catalog, order, billing, or support tool on Plugins and save its Server URL and token. Every tool with that purpose calls the saved address. The token is sent as a bearer header and is not placed in the URL. The client opens an MCP session, keeps that session, and does not follow redirects. A call that the server does not answer fails the run. `MERCHANT_MCP_URL` points every merchant purpose at the local example when no address is saved for that purpose.

`query_sql`, `fetch_url`, `invoke_n8n`, and `use_mcp_server` stay off an agent until their host is saved. Catalog, order, billing, and support tools stay off until their MCP server answers. The agent Tools tab lists every tool and leaves the checkbox off when that host is missing or the contract does not grant the permission.

Once SQL is configured, `query_sql` still returns the local row, and a statement that is not a `SELECT` is rejected. `WEB_ALLOWLIST`, or the web connection string, is the allowlist. The page body stays the local fixture. `invoke_n8n` does not call n8n: `submitted` stays false, `simulated` stays true, and the write still waits for approval. `use_mcp_server` asks the configured MCP server for its tool list. Qdrant and Neo4j follow the same pattern in [Operations](operations.md).

No tool submits a purchase, refund, or dispatch. Approval resumes the simulated write.
