"""Product catalog, comparison, and stock. Writes are not offered."""

from __future__ import annotations

PRODUCTS = {
    "p-jacket-blue": {"product_id": "p-jacket-blue", "name": "Blue trail jacket", "price": 129, "stock": 4, "source_id": "product:p-jacket-blue"},
    "p-boots": {"product_id": "p-boots", "name": "Trail boots", "price": 89, "stock": 0, "source_id": "product:p-boots"},
    "p-lamp": {"product_id": "p-lamp", "name": "Desk lamp", "price": 24, "stock": 12, "source_id": "product:p-lamp"},
}


def search_products(query: str) -> dict:
    tokens = [token for token in query.lower().split() if len(token) > 2]
    found = []
    for product in PRODUCTS.values():
        haystack = f"{product['name']} {product['product_id']}".lower()
        if any(token in haystack for token in tokens):
            found.append(product)
    return {
        "products": found,
        "sources": [{"source_id": item["source_id"], "location": "catalog"} for item in found],
        "explanation": f"Found {len(found)} product(s).",
    }


def get_product_details(product_id: str) -> dict:
    product = PRODUCTS.get(product_id)
    if not product:
        return {"products": [], "explanation": "No matching product.", "sources": []}
    return {
        "products": [product],
        "explanation": f"{product['name']} costs {product['price']}.",
        "sources": [{"source_id": product["source_id"], "location": "catalog"}],
    }


def compare_products(product_ids: list[str]) -> dict:
    items = [PRODUCTS[item] for item in product_ids if item in PRODUCTS]
    return {
        "products": items,
        "explanation": "Compared listed products by price.",
        "sources": [{"source_id": item["source_id"], "location": "catalog"} for item in items],
    }


def check_stock(product_id: str) -> dict:
    product = PRODUCTS.get(product_id, PRODUCTS["p-jacket-blue"])
    return {
        "product_id": product["product_id"],
        "available": product["stock"],
        "explanation": f"{product['name']} has {product['stock']} in stock.",
        "sources": [{"source_id": product["source_id"], "location": "inventory"}],
    }
