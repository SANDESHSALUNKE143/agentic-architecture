"""Client for the optional shared agent API; UI and other services reuse it."""

import re


class RemoteAgent:
    """SDK client for one validated agent ID on an authenticated HTTP transport."""

    def __init__(self, transport, agent_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", agent_id):
            raise ValueError("invalid agent id")
        self.transport = transport
        self.path = "/v1/agents/" + agent_id

    async def ask(self, question):
        """Submit a question to the agent run API and return its JSON run response."""
        return await self.transport.request(
            "POST", self.path + "/runs", body={"question": question}
        )

    async def configuration(self):
        """Read the agent binding configuration snapshot and revision."""
        return await self.transport.request("GET", self.path + "/config")

    async def events(self):
        """Read the credential-scoped run metadata through the agent API."""
        return await self.transport.request("GET", self.path + "/events")
