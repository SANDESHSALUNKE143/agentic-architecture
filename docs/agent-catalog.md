# Agent catalog

These eight specialists are the reference domain. Copy the contract shape for your industry. Every specialist is `agentic/04-loops/specialists/<name>/agent.yaml`. The file is the development contract. LangChain does not own the schema.

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

Follow [Onboard an agent](onboard-agent.md). Copy one contract, export `TOOLS` only when the tool is new, and restart the API. Authentication, logging, errors, and state stay in the shared runtime.
