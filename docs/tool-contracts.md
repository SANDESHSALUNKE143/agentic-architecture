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
| use_mcp_server | mcp_client | no. The address is saved. This process does not call the MCP server |

`check_stock`, `search_documents`, and `analyze_dataset` are registered by `mcp/tool-gateway` from `shared/`. The sales fixture is `shared/fixtures/sales.csv`.

`get_product_details` reads the price from `mcp/catalog-tools/tools.py`. That file is the catalog. It is not an external API and it does not read a website.

Plugins → MCP servers onboards more than one MCP server. Each server has a purpose, a URL, and a token. Check connection sends the MCP initialize call. Those servers do not replace the sample product prices.

`query_sql`, `fetch_url`, `invoke_n8n`, and `use_mcp_server` stay off an agent until their host is saved. The agent Tools tab lists every tool and leaves the checkbox off when that host is missing or the contract does not grant the permission.

Once SQL is configured, `query_sql` still returns the local row, and a statement that is not a `SELECT` is rejected. `WEB_ALLOWLIST`, or the web connection string, is the allowlist. The page body stays the local fixture. `invoke_n8n` does not call n8n: `submitted` stays false, `simulated` stays true, and the write still waits for approval. `use_mcp_server` stores an MCP server address and does not call that server. Qdrant and Neo4j follow the same pattern in [Operations](operations.md).

No tool submits a purchase, refund, or dispatch. Approval resumes the simulated write.
