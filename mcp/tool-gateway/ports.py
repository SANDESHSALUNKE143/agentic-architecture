"""Documents, the sales fixture, and optional SQL, web, and n8n ports."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from urllib.parse import urlparse

from shared.config import ROOT
from shared.memory.corpus import search
from shared.security.redact import strip_untrusted

SALES = ROOT / "shared" / "fixtures" / "sales.csv"


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
        "sources": [{"source_id": "dataset:sales", "location": "shared/fixtures/sales.csv"}],
    }


def query_sql(query: str) -> dict:
    text = query.strip().rstrip(";")
    if not text.lower().startswith("select"):
        return {"rows": [], "explanation": "Only a read-only SELECT is accepted.", "error": "rejected"}
    if os.environ.get("SQL_CONNECTION"):
        return {"rows": [], "explanation": "A SQL connection is configured. This build still returns the local fixture."}
    return {"rows": [{"ok": 1}], "explanation": "Local read-only SQL fixture.", "findings": {"rows": 1}}


def fetch_url(url: str) -> dict:
    host = urlparse(url).hostname or ""
    allow = {item.strip() for item in os.environ.get("WEB_ALLOWLIST", "example.test").split(",") if item.strip()}
    if host not in allow:
        return {"explanation": "Host is not on the allowlist.", "sources": [], "error": "denied"}
    return {
        "explanation": f"Fetched {host} from the local fixture.",
        "sources": [{"source_id": "web:example", "location": url}],
        "answer": "Example catalog page.",
    }


def invoke_n8n(path: str, approved: bool = False) -> dict:
    base = os.environ.get("N8N_BASE_URL", "")
    return {
        "path": path,
        "base_configured": bool(base),
        "approved": approved,
        "submitted": False,
        "simulated": True,
        "explanation": "n8n was not called. The workflow waits for approval.",
    }
