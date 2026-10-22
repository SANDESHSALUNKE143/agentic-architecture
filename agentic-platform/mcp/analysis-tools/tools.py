"""Stats on the bundled CSV. Caller code is never executed."""

from __future__ import annotations

import csv
from pathlib import Path

CSV_PATH = Path(__file__).parent / "fixtures" / "sales.csv"


async def analyze_dataset(ctx, arguments):
    reference = arguments.get("dataset_reference", "sales")
    if reference != "sales":
        return {"error": "unknown dataset", "simulated": True}
    code = arguments.get("code")
    if code:
        return {"error": "arbitrary code is not accepted", "simulated": True}
    amounts = []
    units = []
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            amounts.append(float(row["amount"]))
            units.append(int(row["units"]))
    count = len(amounts)
    return {
        "dataset": "sales",
        "count": count,
        "unit_total": sum(units),
        "amount_mean": round(sum(amounts) / count, 2) if count else 0,
        "simulated": True,
    }
