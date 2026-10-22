"""Local routing examples. They never add a tool or skip approval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.contracts import new_id


class Learning:
    def __init__(self, data_dir: Path) -> None:
        self.path = Path(data_dir) / "learning.json"
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _rows(self) -> list[dict[str, Any]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, rows: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def add_feedback(self, run_id: str, rating: str, note: str) -> dict[str, Any]:
        if rating not in {"helpful", "not_helpful"}:
            raise ValueError("rating must be helpful or not_helpful")
        rows = self._rows()
        feedback = {
            "id": new_id("fb"),
            "run_id": run_id,
            "rating": rating,
            "note": note.strip(),
        }
        rows.append({"kind": "feedback", **feedback})
        if rating == "not_helpful" and "catalog" in note.lower():
            rows.append(
                {
                    "kind": "example",
                    "id": feedback["id"],
                    "match": "jacket",
                    "workflow": None,
                    "agents": ["catalog-agent"],
                    "note": note.strip(),
                }
            )
        self._save(rows)
        return feedback

    def feedback_for_run(self, run_id: str) -> list[dict[str, Any]]:
        return [
            row
            for row in self._rows()
            if row.get("kind") == "feedback" and row.get("run_id") == run_id
        ]

    def match_example(self, task: str) -> dict[str, Any] | None:
        """Return a learned route when the task shares the example's keyword."""
        lowered = task.lower()
        for row in self._rows():
            if row.get("kind") == "example" and row.get("match") and row["match"] in lowered:
                return row
        return None
