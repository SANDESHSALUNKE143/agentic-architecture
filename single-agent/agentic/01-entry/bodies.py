"""JSON body for one desk-agent run.

Purpose: FastAPI checks the task and the session before the harness runs.
Used by: agentic/01-entry/app.py.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HarnessBody(BaseModel):
    harness: str = Field(description="langchain, claude, or deepagent.")


class RunBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"task": "Find a blue trail jacket under $150"}})
    task: str = Field(description="The brief for desk-agent.")
    user_id: str = Field(default="local-development-user", description="Who the run is for.")
    session_id: str = Field(default="", description="Conversation id. Empty starts a new session.")
