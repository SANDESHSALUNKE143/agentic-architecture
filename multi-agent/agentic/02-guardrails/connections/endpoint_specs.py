"""Known connector addresses.

Purpose: the list of hosts the console can save. The password store is endpoints.py.
Used by: agentic/02-guardrails/connections/endpoints.py.
"""

from __future__ import annotations

ENDPOINTS: list[dict[str, str]] = [
    {
        "id": "n8n",
        "title": "n8n",
        "group": "Automation",
        "summary": "This repository does not host n8n. Enter the URL of the n8n you run.",
        "env_url": "N8N_BASE_URL",
        "env_secret": "N8N_TOKEN",
    },
    {
        "id": "grafana",
        "title": "Grafana",
        "group": "Observability",
        "summary": "The Grafana address where dashboards and traces are opened.",
        "env_url": "GRAFANA_URL",
        "env_secret": "GRAFANA_PASSWORD",
    },
    {
        "id": "otlp",
        "title": "OpenTelemetry",
        "group": "Observability",
        "summary": "The collector that receives traces.",
        "env_url": "OTEL_EXPORTER_OTLP_ENDPOINT",
        "env_secret": "",
    },
    {
        "id": "log_store",
        "title": "Log store",
        "group": "Observability",
        "summary": "The store that will read the trace export.",
        "env_url": "OBSERVABILITY_LOG_URL",
        "env_secret": "",
    },
    {
        "id": "qdrant",
        "title": "Qdrant",
        "group": "RAG",
        "summary": "The vector database URL used when an agent selects Qdrant.",
        "env_url": "QDRANT_URL",
        "env_secret": "QDRANT_API_KEY",
    },
    {
        "id": "aws_vector",
        "title": "AWS vector",
        "group": "RAG",
        "summary": "The AWS vector endpoint. Use the access key as the username and the secret key as the password.",
        "env_url": "AWS_VECTOR_ENDPOINT",
        "env_secret": "AWS_SECRET_ACCESS_KEY",
    },
    {
        "id": "embedding",
        "title": "Embedding model",
        "group": "RAG",
        "summary": "The direct URL of the embedding model host.",
        "env_url": "EMBEDDING_BASE_URL",
        "env_secret": "EMBEDDING_API_KEY",
    },
    {
        "id": "model",
        "title": "Model host",
        "group": "RAG",
        "summary": "The direct URL of the chat model host.",
        "env_url": "MODEL_BASE_URL",
        "env_secret": "MODEL_API_KEY",
    },
    {
        "id": "sql",
        "title": "SQL",
        "group": "Data",
        "summary": "The database connection string. A string saved here is shown again. A string set only in the environment is not shown.",
        "env_url": "",
        "env_secret": "",
        "env_name": "SQL_CONNECTION",
    },
    {
        "id": "web",
        "title": "Web allowlist",
        "group": "Connections",
        "summary": "Hosts that fetch_url may read. Put the hosts in the connection string, separated by commas.",
        "env_url": "",
        "env_secret": "",
        "env_name": "WEB_ALLOWLIST",
    },
    {
        "id": "mcp",
        "title": "MCP server",
        "group": "MCP",
        "summary": "Address of an MCP server run by another application. use_mcp_server lists that server's tools. Product, order, billing, and support tools call the server onboarded for their purpose.",
        "env_url": "MCP_SERVER_URL",
        "env_secret": "MCP_SERVER_TOKEN",
    },
    {
        "id": "neo4j",
        "title": "Neo4j",
        "group": "Data",
        "summary": "The graph database URL, username, and password.",
        "env_url": "NEO4J_URL",
        "env_secret": "NEO4J_PASSWORD",
    },
]
