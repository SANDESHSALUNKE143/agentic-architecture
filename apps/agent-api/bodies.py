"""JSON bodies the console is allowed to send.

Purpose: FastAPI checks these fields before a route runs. The descriptions appear on /docs.
Used by: the route modules in this folder. A new screen that posts JSON adds a class here.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RunBody(BaseModel):
    """Starts one run. Chat sends this to /agent-runs and /agent-runs/stream."""

    model_config = ConfigDict(json_schema_extra={"example": {"task": "Find a blue trail jacket under $150"}})
    task: str = Field(description="The brief. Phrases select a workflow when workflow and agents are empty.")
    user_id: str = Field(default="local-development-user", description="Who the run is for.")
    session_id: str = Field(default="", description="Conversation id. Empty starts a new session.")
    workflow: str | None = Field(default=None, description="A sequence name, such as product-discovery, or a specialist such as research.")
    agents: list[str] | None = Field(default=None, description="Explicit agent list. When set, it wins over workflow and over phrase matching.")


class DecisionBody(BaseModel):
    """Approves or rejects one paused write. The Approvals page sends this."""

    decision: str = Field(description="approve or reject.")
    actor: str = Field(default="local-operator", description="Who decides. This must differ from the agent that asked.")


class FeedbackBody(BaseModel):
    """Records whether an answer helped. It does not change model weights."""

    helpful: bool = Field(description="True when the operator accepts the answer.")
    note: str = Field(default="", description="Optional note, kept short by the evaluation log.")


class ContractBody(BaseModel):
    """Partial agent contract. The gear and Configuration page send the fields they change."""

    instructions: list[str] | None = Field(default=None, description="Contract lines. Omitted leaves the file unchanged.")
    tools: list[str] | None = Field(default=None, description="Plugin names the agent may call.")
    memory: dict | None = Field(default=None, description="Conversation state, notes, and long_term_memory.")
    approval: dict | None = Field(default=None, description="required_for, and amount_gte on the order contract.")
    permissions: dict | None = Field(default=None, description="Flags such as catalog_read. A write flag cannot be granted here.")
    observability: list[str] | None = Field(default=None, description="Sink ids, including platform_trace and evaluation.")
    rag: dict | None = Field(default=None, description="retrieve, capture, vector, and embedding.")
    model: dict | None = Field(default=None, description="provider: platform, an OpenAI-compatible host, or AWS.")


class NoteBody(BaseModel):
    """One redacted note. POST /memory/notes stores it for later retrieval."""

    user_id: str = Field(description="Whose note this is.")
    text: str = Field(max_length=500, description="At most 500 characters.")


class PluginBody(BaseModel):
    """Agents that may use one plugin, RAG choice, or observability sink."""

    agents: list[str] = Field(description="Agent ids that already have the matching permission.")


class McpServerBody(BaseModel):
    """One MCP server this process may be pointed at. The password is stored and is not returned."""

    title: str = Field(description="Name shown in the console, such as Product catalog.")
    purpose: str = Field(default="product", description="product, orders, billing, support, research, or other.")
    url: str = Field(description="http or https address of the MCP server.")
    username: str = Field(default="", description="Optional account name.")
    password: str = Field(default="", description="Bearer token or password. Blank keeps the stored secret.")


class EndpointBody(BaseModel):
    """A connector address. The password is stored and is not returned."""

    url: str = Field(default="", description="Direct URL of the system you already run.")
    connection_string: str = Field(default="", description="SQL or other connection string.")
    username: str = Field(default="", description="Account name. For AWS this is the access key id.")
    password: str = Field(default="", description="Secret. Blank keeps the password already stored.")
