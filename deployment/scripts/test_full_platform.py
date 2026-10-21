"""Acceptance test against the local Docker stack; never prints credentials or content."""

import json
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
secrets = {
    line.split("=", 1)[0]: line.split("=", 1)[1]
    for line in (ROOT / "deployment/full/.env").read_text().splitlines()
    if "=" in line and not line.startswith("#")
}


def call(path, body=None, token="PLATFORM_AGENT_TOKEN", method=None, port=8020, expected=200):
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": "Bearer " + secrets[token]} if token else {}),
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        status = exc.code
        result = json.load(exc)
    assert status == expected, (path, status, expected)
    return result


def main():
    call("/health", token=None)
    call("/v1/cost/usage", token=None, expected=401)
    config = json.loads((Path(secrets["AGENTN_SOURCE"]) / "config/agentn-demo.json").read_text())
    try:
        current = call("/v1/registry/config")["revision"]
    except AssertionError:
        current = 0
    published = call(
        "/v1/registry/config",
        {"expected_revision": current, "config": config},
        method="PUT",
    )
    assert published["revision"] == current + 1
    call(
        "/v1/registry/config",
        {"expected_revision": current, "config": config},
        method="PUT",
        expected=409,
    )
    call("/v1/registry/config", token="PLATFORM_OTHER_TOKEN", expected=404)
    call(
        "/v1/registry/config",
        {"expected_revision": 0, "config": config},
        token="PLATFORM_OTHER_TOKEN",
        method="PUT",
        expected=403,
    )
    document = {
        "document_id": "synthetic-" + uuid.uuid4().hex,
        "text": "Synthetic readiness guide: catalog and freshness must be checked before reporting.",
    }
    queued = call("/v1/knowledge/documents", document, expected=202)
    duplicate = call("/v1/knowledge/documents", document, expected=202)
    assert queued["id"] == duplicate["id"]
    for _ in range(40):
        job = call("/v1/knowledge/jobs/" + queued["id"])
        if job["state"] != "pending":
            break
        time.sleep(1)
    assert job["state"] == "complete", job
    call("/v1/knowledge/jobs/" + queued["id"], token="PLATFORM_OTHER_TOKEN", expected=404)
    assert call("/v1/knowledge/search", {"question": "readiness catalog freshness"})["hits"]
    assert not call(
        "/v1/knowledge/search",
        {"question": "readiness catalog freshness"},
        token="PLATFORM_OTHER_TOKEN",
    )["hits"]
    call(
        "/v1/tools/list_tables",
        {"arguments": {}},
        token="PLATFORM_OTHER_TOKEN",
        expected=403,
    )
    result = call(
        "/v1/agents/advertising-assistant/runs",
        {"question": "Is the data ready?"},
        token="AGENT_API_TOKEN",
        port=8010,
    )
    assert result["tools_used"] == ["list_tables", "get_data_status"]
    assert "DEMO" in result["answer"]
    ledger = call("/v1/cost/usage")["usage"]
    assert ledger and ledger[0]["calls"] >= 3 and ledger[0]["reserved"] > 0
    assert not call("/v1/cost/usage", token="PLATFORM_OTHER_TOKEN")["usage"]
    print(
        "PASS: registry revision conflict, credential/scope isolation, queued/idempotent ingestion, Qdrant retrieval, hosted AgentN model/tools, durable token ledger."
    )
    print("Synthetic acceptance run:", result["run_id"])


if __name__ == "__main__":
    main()
