"""Documents, the sales file, and the SQL, web, and n8n ports.

Purpose: answer from local fixtures. SQL, web, and n8n record that a host is configured and still use the local stand-in.
Used by: agentic/05-tools/mcp/tool-gateway/registry.py. Replace the body of invoke_n8n here when a real webhook should be posted after approval.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from urllib.parse import urlparse

from agentic.platform.config import ROOT
from guardrails.policy.redact import strip_untrusted
from loops.memory.corpus import search

SALES = ROOT / "agentic" / "04-loops" / "memory" / "fixtures" / "sales.csv"


def search_documents(query: str) -> dict:
    hits = search(query)
    if not hits:
        return {
            "answer": "The indexed sources do not establish an answer.",
            "sources": [],
            "explanation": "No document matched.",
        }
    snippets = [strip_untrusted(hit["snippet"]) for hit in hits]
    return {
        "answer": snippets[0],
        "sources": [{"source_id": hit["source_id"], "location": hit["location"]} for hit in hits],
        "explanation": "Answer is limited to indexed documents.",
    }


def analyze_dataset(dataset_reference: str, code: str = "") -> dict:
    lowered = code.lower()
    if any(token in lowered for token in ("exec", "import ", "open(", "__")):
        return {"findings": {}, "explanation": "The analysis request was rejected.", "sources": [], "error": "rejected"}
    path = SALES if dataset_reference == "sales" else Path(dataset_reference)
    if not path.exists():
        return {"findings": {}, "explanation": "Dataset was not found.", "sources": []}
    amounts = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            amounts.append(float(row["amount"]))
    mean = round(sum(amounts) / len(amounts), 2) if amounts else 0
    return {
        "findings": {"rows": len(amounts), "mean_amount": mean},
        "explanation": f"Mean amount is {mean}.",
        "sources": [{"source_id": "dataset:sales", "location": "agentic/04-loops/memory/fixtures/sales.csv"}],
    }


def query_sql(query: str) -> dict:
    text = query.strip().rstrip(";")
    if not text.lower().startswith("select"):
        return {"rows": [], "explanation": "Only a read-only SELECT is accepted.", "error": "rejected"}
    if os.environ.get("SQL_CONNECTION"):
        return {"rows": [], "explanation": "A SQL connection is configured. This build still returns the local fixture."}
    return {"rows": [{"ok": 1}], "explanation": "Local read-only SQL fixture.", "findings": {"rows": 1}}


def fetch_url(url: str) -> dict:
    from guardrails.connections.endpoints import saved

    host = urlparse(url).hostname or ""
    saved_list = str(saved("web").get("connection_string") or "").strip()
    raw = saved_list or os.environ.get("WEB_ALLOWLIST", "example.test")
    allow = {item.strip() for item in raw.split(",") if item.strip()}
    if host not in allow:
        return {"explanation": "Host is not on the allowlist.", "sources": [], "error": "denied"}
    return {
        "explanation": f"Fetched {host} from the local fixture.",
        "sources": [{"source_id": "web:example", "location": url}],
        "answer": "Example catalog page.",
    }


def use_mcp_server(tool_name: str = "") -> dict:
    from agentic.platform.config import ROOT
    from agentic.platform.loader import load_module

    client = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "client.py", "merchant_mcp_client")
    listed = client.list_tools()
    listed["tool_name"] = tool_name
    return listed


def invoke_n8n(path: str, approved: bool = False) -> dict:
    from guardrails.connections.endpoints import target

    hosted = bool(target("n8n", "N8N_BASE_URL"))
    return {
        "path": path,
        "base_configured": hosted,
        "approved": approved,
        "submitted": False,
        "simulated": True,
        "explanation": "n8n was not called. This repository does not host n8n. Set its URL in connection configuration. Writes still wait for approval.",
    }


TOOLS = {
    "search_documents": {
        "group": "Research",
        "summary": "Answers from the local document index.",
        "permission": "research_read",
        "write": False,
        "fn": search_documents,
        "schema": {"query": "string"},
    },
    "analyze_dataset": {
        "group": "Analysis",
        "summary": "Summarizes the local sales fixture.",
        "permission": "analysis_read",
        "write": False,
        "fn": analyze_dataset,
        "schema": {"dataset_reference": "string"},
    },
    "query_sql": {
        "group": "Connections",
        "summary": "Runs a read-only SELECT. Writes are rejected.",
        "permission": "sql_read",
        "write": False,
        "endpoint": "sql",
        "fn": query_sql,
        "schema": {"query": "string"},
    },
    "fetch_url": {
        "group": "Connections",
        "summary": "Reads a page only when the host is allowlisted.",
        "permission": "web_read",
        "write": False,
        "endpoint": "web",
        "fn": fetch_url,
        "schema": {"url": "string"},
    },
    "invoke_n8n": {
        "group": "Connections",
        "summary": "Simulates an n8n call and waits for approval.",
        "permission": "n8n_write",
        "write": True,
        "endpoint": "n8n",
        "fn": invoke_n8n,
        "schema": {"path": "string"},
    },
    "use_mcp_server": {
        "group": "MCP",
        "summary": "Lists the tools published by a configured MCP server.",
        "permission": "mcp_client",
        "write": False,
        "endpoint": "mcp",
        "fn": use_mcp_server,
        "schema": {"tool_name": "string"},
    },
}
