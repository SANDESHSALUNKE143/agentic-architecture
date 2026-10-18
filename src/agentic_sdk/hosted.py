"""Compatibility entrypoints for platform API and worker."""

from agentic_sdk.adapters.persistence.postgres import Database
from agentic_sdk.services.app import create_app
from agentic_sdk.services.contracts import (
    Body,
    Decision,
    Ingestion,
    Registration,
    Search,
    ToolCall,
)
from agentic_sdk.services.knowledge_service.components import components
from agentic_sdk.services.knowledge_service.worker import work_once, worker

if __name__ == "__main__":
    worker()
