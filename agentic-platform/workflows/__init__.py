"""Named workflows. The engine reads the same ids from the router."""

WORKFLOWS = {
    "product-discovery": ["shopping-agent", "catalog-agent", "inventory-agent"],
    "customer-support": ["customer-service-agent", "support-agent", "billing-agent"],
    "order-processing": ["order-agent", "billing-agent"],
    "field-response": [
        "coordinator-agent",
        "satellite-agent",
        "social-media-agent",
        "simulation-agent",
        "logistics-agent",
    ],
}
