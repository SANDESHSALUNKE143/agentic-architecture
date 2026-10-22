"""Search the mock catalog and remember the chosen product id."""

from agents.base import Agent, finish

AGENT = Agent(
    id="catalog-agent",
    display_name="Catalog",
    description="Search the catalog and return product details.",
    instructions="Use search_products and get_product_details. Cite only tool results.",
    allowed_tools=("search_products", "get_product_details"),
    permissions=("catalog:read",),
    approval_policy="none",
    sample_task="Find a blue trail jacket",
)


async def handle(step, observations):
    notes = step.long_term_notes()
    query = step.previous("query") or step.task
    found = await step.call_tool("search_products", {"query": query})
    products = found["result"].get("products", []) if found["ok"] else []
    if not products:
        return finish("No matching products.", {"products": [], "notes": notes})
    top = products[0]
    details = await step.call_tool("get_product_details", {"product_id": top["id"]})
    product = details["result"].get("product", top)
    step.remember("product_id", product["id"])
    step.remember("query", query)
    summary = f"Found {product['name']}."
    if notes:
        summary += f" Long-term note {notes[0]['id']} matches this request."
    return finish(
        summary, {"product": product, "products": products, "notes": notes, "query": query}
    )


AGENT.handler = handle
