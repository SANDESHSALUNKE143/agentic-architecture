"""Closed, bounded HTTP input models shared by platform routes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Body(BaseModel):
    """Base API input model rejecting unknown fields."""

    model_config = ConfigDict(extra="forbid")


class Registration(Body):
    """Configuration publication with an expected revision for stale-write protection."""

    expected_revision: int = Field(ge=0)
    config: dict


class Ingestion(Body):
    """One bounded, already-chunked document submitted to the persistent worker queue."""

    document_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    text: str = Field(min_length=1, max_length=16000)


class Search(Body):
    """Scoped knowledge query with a bounded number of requested matches."""

    question: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=3, ge=1, le=20)


class Decision(Body):
    """Bounded model-gateway request containing instructions, evidence and approved tools."""

    instruction: str = Field(max_length=16000)
    question: str = Field(min_length=1, max_length=8000)
    observations: list[dict] = Field(max_length=32)
    tools: list[dict] = Field(max_length=64)
    max_output_tokens: int = Field(ge=64, le=8192)


class ToolCall(Body):
    """Arguments for a tool selected from the server allowlist."""

    arguments: dict = Field(default_factory=dict)
