# Agent catalog

These eight specialists are the reference domain. Copy the contract shape for your industry. Every specialist is `agents/<name>/agent.yaml`. The file is the development contract. LangChain does not own the schema.

| Agent | Reads | Tools | Write approval |
| --- | --- | --- | --- |
| catalog-agent | catalog, inventory | search_products, get_product_details, compare_products | none |
| shopping-agent | catalog | search_products, compare_products | none |
| support-agent | orders | get_order_status, request_approval | request_approval |
| inventory-agent | inventory | check_stock | none |
| order-agent | catalog, orders | prepare_order | prepare_order when amount is at least `amount_gte` (default 100) |
| billing-agent | billing | get_eligible_discounts | none |
| data-analysis-agent | analysis | analyze_dataset | none |
| research-agent | documents | search_documents | none |

`long_term_memory: optional` means the agent may read a saved note and must not invent a memory it did not retrieve.

`rag.retrieve` means the agent reads the retrieval index. `rag.capture` means it stores a redacted note. Research reads. The others do not. Vector and embedding choices include AWS. The model provider is platform, OpenAI-compatible, or AWS Bedrock.

The sequences the planner can require are in [Workflows](workflows.md).

- `product-discovery`: shopping, catalog, inventory
- `customer-support`: support, billing
- `order-processing`: order, billing

## Add an agent

1. Copy `agents/catalog-agent/agent.yaml` to `agents/<name>/agent.yaml`.
2. List only tools that already exist in the gateway registry.
3. Set permissions the gateway already understands, and an `output_schema`.
4. Add one case under `tests/agent-evaluation/cases.json`.
5. Restart the API. Authentication, logging, errors, and state stay in the shared runtime.
