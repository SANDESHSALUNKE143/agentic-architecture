"""Three stores: scratchpad, approved notes, and the document index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.contracts import digest, new_id
from shared.memory.rag import Retrieval


class Memory:
    """Scratchpad rows die with the session. Notes survive only after approval."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_path = self.data_dir / "notes.json"
        self.short: dict[str, dict[str, Any]] = {}
        self.retrieval = Retrieval()
        if not self.notes_path.exists():
            self.notes_path.write_text("[]", encoding="utf-8")

    def remember(self, session_id: str, key: str, value: Any) -> None:
        self.short.setdefault(session_id, {})[key] = value

    def recall(self, session_id: str, key: str, default: Any = None) -> Any:
        return self.short.get(session_id, {}).get(key, default)

    def session_view(self, session_id: str) -> dict[str, Any]:
        return dict(self.short.get(session_id, {}))

    def clear_session(self, session_id: str) -> None:
        self.short.pop(session_id, None)

    def list_notes(self) -> list[dict[str, Any]]:
        return json.loads(self.notes_path.read_text(encoding="utf-8"))

    def stage_note(self, text: str, user_id: str) -> dict[str, Any]:
        """Build the approval payload. Nothing is written until commit_note."""
        payload = {"text": text.strip(), "user_id": user_id}
        return {
            "action": "save_note",
            "summary": f"Save note: {text.strip()[:120]}",
            "params": payload,
            "params_hash": digest(payload),
        }

    def commit_note(self, params: dict[str, Any]) -> dict[str, Any]:
        notes = self.list_notes()
        note = {
            "id": new_id("mem"),
            "text": params["text"],
            "user_id": params.get("user_id", ""),
        }
        notes.append(note)
        self.notes_path.write_text(json.dumps(notes, indent=2), encoding="utf-8")
        return note

    def search_notes(self, query: str) -> list[dict[str, Any]]:
        words = [word for word in query.lower().split() if len(word) > 3]
        found = []
        for note in self.list_notes():
            text = note["text"].lower()
            if any(word in text for word in words):
                found.append(note)
        return found
