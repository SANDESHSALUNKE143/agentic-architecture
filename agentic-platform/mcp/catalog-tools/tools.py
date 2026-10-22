"""Mock catalog. Every row is labelled simulated."""

from __future__ import annotations

STOCK = {
    "p-jacket-blue": 4,
    "p-boots": 0,
    "p-lamp": 12,
}

PRODUCTS = {
    "p-jacket-blue": {
        "id": "p-jacket-blue",
        "name": "Blue trail jacket",
        "price": 129,
        "color": "blue",
        "tags": ["jacket", "trail", "hiking"],
    },
    "p-boots": {
        "id": "p-boots",
        "name": "Hiking boots",
        "price": 89,
        "color": "brown",
        "tags": ["boots", "hiking"],
    },
    "p-lamp": {
        "id": "p-lamp",
        "name": "Camp lamp",
        "price": 24,
        "color": "yellow",
        "tags": ["lamp", "camp"],
    },
}


async def search_products(ctx, arguments):
    query = str(arguments.get("query", "")).lower()
    parts = [part for part in query.split() if len(part) > 2]
    found = []
    for product in PRODUCTS.values():
        haystack = " ".join([product["name"], product["color"], *product["tags"]]).lower()
        if not parts or any(part in haystack for part in parts):
            found.append({k: v for k, v in product.items() if k != "tags"})
    return {"products": found, "simulated": True}


async def get_product_details(ctx, arguments):
    product = PRODUCTS.get(arguments["product_id"])
    if product is None:
        return {"product": None, "simulated": True, "found": False}
    return {"product": product, "simulated": True, "found": True}


async def check_stock(ctx, arguments):
    product_id = arguments["product_id"]
    if product_id not in STOCK:
        return {"product_id": product_id, "found": False, "simulated": True}
    available = STOCK[product_id]
    return {
        "product_id": product_id,
        "available": available,
        "in_stock": available > 0,
        "simulated": True,
    }


async def compare_prices(ctx, arguments):
    product = PRODUCTS.get(arguments["product_id"])
    if product is None:
        return {"offers": [], "simulated": True}
    price = product["price"]
    return {
        "product_id": product["id"],
        "offers": [
            {"seller": "Northwind", "price": price},
            {"seller": "Contoso", "price": price + 8},
        ],
        "simulated": True,
    }
