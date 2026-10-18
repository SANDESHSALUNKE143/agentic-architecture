"""Run inside the platform container to verify telemetry and atomic reservations."""

import json
import os
import time
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

from agentic_sdk.contracts import Context
from fastapi import HTTPException

from agentic_sdk.hosted import Database


def main():
    db = Database(os.environ["DATABASE_URL"])
    ctx = Context("acceptance-" + uuid.uuid4().hex, "quota-test", frozenset())

    def reserve(_):
        try:
            db.reserve(ctx, 10, 50)
            return True
        except HTTPException as error:
            assert error.status_code == 429
            return False

    try:
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(reserve, range(20)))
        assert sum(results) == 5, results
        with db.connect() as connection:
            assert (
                connection.execute(
                    "SELECT reserved FROM token_ledger WHERE tenant=%s AND agent=%s",
                    (ctx.tenant_id, ctx.agent_id),
                ).fetchone()["reserved"]
                == 50
            )
    finally:
        with db.connect() as connection:
            connection.execute(
                "DELETE FROM token_ledger WHERE tenant=%s AND agent=%s",
                (ctx.tenant_id, ctx.agent_id),
            )
    urls = {
        "metrics": "http://prometheus:9090/api/v1/query?query=agentic_events_total",
        "logs": "http://loki:3100/loki/api/v1/query_range?query=%7Bservice_name%3D%22agentic-platform%22%7D",
        "traces": "http://tempo:3200/api/search",
    }
    for name, url in urls.items():
        # Exporters batch asynchronously; acceptance must allow bounded delivery time.
        for attempt in range(15):
            with urllib.request.urlopen(url, timeout=10) as response:
                result = json.load(response)
            values = (
                result.get("traces", [])
                if name == "traces"
                else result.get("data", {}).get("result", [])
            )
            if values:
                break
            time.sleep(2)
        assert values, name + " missing"
        print("PASS:", name, "received telemetry")
    print(
        "PASS: 20 concurrent quota requests admit exactly 5 reservations; remaining requests denied."
    )


if __name__ == "__main__":
    main()
