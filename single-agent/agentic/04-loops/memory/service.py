"""Session turns and optional notes.

Purpose: keep conversation state for a session, and store a note only when the caller asks. Tool results stay on the run.
Used by: agentic/04-loops/runtime/runtime.py and POST /memory/notes.
"""

from __future__ import annotations

from loops.memory.corpus import accept_citations, graph_search, search


class MemoryService:
    def __init__(self) -> None:
        self.sessions: dict[str, list[dict]] = {}
        self.notes: list[dict] = []

    def remember(self, session_id: str, role: str, text: str) -> None:
        self.sessions.setdefault(session_id, []).append({"role": role, "text": text[:500]})

    def history(self, session_id: str) -> list[dict]:
        return list(self.sessions.get(session_id, []))

    def add_note(self, user_id: str, text: str) -> dict:
        note = {"user_id": user_id, "text": text[:500]}
        self.notes.append(note)
        return note

    def find_notes(self, user_id: str, query: str) -> list[dict]:
        tokens = [token for token in query.lower().split() if len(token) > 3]
        return [
            note
            for note in self.notes
            if note["user_id"] == user_id and any(token in note["text"].lower() for token in tokens)
        ]

    def retrieve(self, query: str) -> list[dict]:
        return search(query) + graph_search(query)

    def citations(self, items: list[dict]) -> list[dict]:
        return accept_citations(items)
