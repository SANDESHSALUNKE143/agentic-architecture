"""Read sensors and recommend irrigation. Opening a valve waits for approval."""

from agents.base import Agent, finish

AGENT = Agent(
    id="agriculture-agent",
    display_name="Agriculture",
    description="Read sensors and recommend irrigation. The valve stays closed.",
    instructions="Call read_sensors. Actuation requires approval and stays simulated.",
    allowed_tools=("read_sensors", "irrigate"),
    permissions=("field:read", "field:write"),
    approval_policy="physical actuation requires approval",
    sample_task="Check soil moisture and recommend irrigation",
    read_only=False,
)


async def handle(step, observations):
    reading = await step.call_tool("read_sensors", {"field": "north-plot"})
    moisture = reading["result"].get("soil_moisture")
    recommendation = (
        "Recommend irrigation."
        if isinstance(moisture, int) and moisture < 20
        else "No irrigation recommended."
    )
    if "open" not in step.task.lower() and "actuate" not in step.task.lower():
        return finish(recommendation, {"sensors": reading["result"], "valve_opened": False})
    pending = {"name": "irrigate", "arguments": {"field": "north-plot"}}
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        recommendation + " Opening the valve is waiting for approval.",
        {"sensors": reading["result"], "valve_opened": False},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle
