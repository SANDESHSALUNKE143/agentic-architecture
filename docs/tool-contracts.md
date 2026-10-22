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

`check_stock`, `search_documents`, and `analyze_dataset` are registered by `mcp/tool-gateway` from `shared/`. The sales fixture is `shared/fixtures/sales.csv`.

`SQL_CONNECTION` marks SQL configured. `query_sql` still returns the local row, and a statement that is not a `SELECT` is rejected. `WEB_ALLOWLIST` denies any other host. The page body stays the local fixture. `N8N_BASE_URL` marks n8n configured. `invoke_n8n` does not call n8n: `submitted` stays false, `simulated` stays true, and the write still waits for approval. `N8N_TOKEN` stays in the API environment. Qdrant and Neo4j follow the same pattern in [Operations](operations.md).

No tool submits a purchase, refund, or dispatch. Approval resumes the simulated write.
