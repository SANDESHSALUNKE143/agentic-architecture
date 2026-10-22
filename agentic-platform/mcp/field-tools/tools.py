"""Field examples. Physical actions and dispatch stay simulated."""

from __future__ import annotations


async def analyze_imagery(ctx, arguments):
    return {
        "scene": arguments.get("scene", "river-south"),
        "summary": "Simulated imagery shows a clear staging field south of the river.",
        "simulated": True,
    }


async def search_feed(ctx, arguments):
    return {
        "posts": [
            {
                "id": "post-1",
                "text": "Road south of the river is open.",
                "approved_source": True,
            }
        ],
        "simulated": True,
    }


async def run_simulation(ctx, arguments):
    return {
        "hazard": arguments.get("hazard", "aftershock"),
        "risk": "elevated",
        "window_hours": 48,
        "simulated": True,
    }


async def prepare_dispatch(ctx, arguments):
    return {
        "dispatch_id": "disp-1",
        "destination": arguments.get("destination", "river-south"),
        "sent": False,
        "simulated": True,
    }


async def prepare_purchase_order(ctx, arguments):
    return {
        "po_id": "po-1",
        "sku": arguments.get("sku", "p-jacket-blue"),
        "sent": False,
        "simulated": True,
    }


async def read_sensors(ctx, arguments):
    return {
        "field": arguments.get("field", "north-plot"),
        "soil_moisture": 18,
        "weather": "dry",
        "simulated": True,
    }


async def irrigate(ctx, arguments):
    return {
        "field": arguments.get("field", "north-plot"),
        "valve_opened": False,
        "simulated": True,
    }


async def health_info(ctx, arguments):
    return {
        "topic": arguments.get("topic", "general"),
        "summary": "This is general information, not a diagnosis or a treatment.",
        "requires_qualified_review": True,
        "simulated": True,
    }
