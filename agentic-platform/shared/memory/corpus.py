"""Small local document set. Citations point at these ids."""

from __future__ import annotations

DOCUMENTS = (
    {
        "id": "doc-jackets",
        "title": "Trail jacket",
        "entity": "Jacket",
        "text": (
            "The blue trail jacket is water resistant and weighs 400 grams. "
            "Product id p-jacket-blue. It is stocked for hiking."
        ),
    },
    {
        "id": "doc-returns",
        "title": "Returns",
        "entity": "Returns",
        "text": "Orders can be refunded within 30 days while the order is open. Order 1001 is open.",
    },
    {
        "id": "doc-irrigation",
        "title": "Field notes",
        "entity": "Field",
        "text": "Soil moisture below 20 percent is a reason to recommend irrigation, not to open a valve.",
    },
)

GRAPH = {
    "Jacket": [
        {"relation": "COLOR", "target": "Blue", "passage": "The trail jacket color is blue."},
        {"relation": "FABRIC", "target": "Nylon", "passage": "The trail jacket shell is nylon."},
        {"relation": "PRODUCT", "target": "p-jacket-blue", "passage": "Catalog id p-jacket-blue."},
    ],
    "Earthquake": [
        {
            "relation": "RISK",
            "target": "Aftershock",
            "passage": "Aftershock risk is elevated for 48 hours.",
        },
        {
            "relation": "TEAM",
            "target": "Logistics",
            "passage": "Logistics staging is south of the river.",
        },
    ],
    "Returns": [
        {
            "relation": "WINDOW",
            "target": "30 days",
            "passage": "The refund window is 30 days for open orders.",
        },
    ],
}
