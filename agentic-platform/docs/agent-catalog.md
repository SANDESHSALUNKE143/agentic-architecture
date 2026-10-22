# Agent catalog

See [developer-guide.md](developer-guide.md) for the sample command for each id.

| Id | Tools | Approval |
| --- | --- | --- |
| catalog-agent | search_products, get_product_details | none |
| shopping-agent | none | none; does not order |
| customer-service-agent | none | none |
| support-agent | get_order_status, request_approval | refund |
| inventory-agent | check_stock | none |
| order-agent | prepare_order | submit |
| billing-agent | get_eligible_discounts | none |
| personal-shopping-agent | compare_prices, prepare_order | purchase |
| data-analysis-agent | analyze_dataset | none; no caller code |
| research-agent | search_documents, expand_entity | none |
| scientific-research-agent | search_literature, expand_entity | none; simulated literature |
| enterprise-admin-agent | prepare_provisioning | provisioning |
| software-agent | propose_patch, apply_patch | file write stays dry-run |
| marketing-agent | draft_campaign, request_approval | send |
| coordinator-agent | none | dispatch stays with logistics |
| satellite-agent | analyze_imagery | none; simulated |
| social-media-agent | search_feed | none |
| simulation-agent | run_simulation | none; simulated |
| logistics-agent | prepare_dispatch | dispatch |
| supplier-agent | prepare_purchase_order | send |
| agriculture-agent | read_sensors, irrigate | valve stays closed until approval |
| healthcare-agent | health_info | qualified review; no diagnosis |

The router lives in `orchestrator/router`, not under `agents/`.
