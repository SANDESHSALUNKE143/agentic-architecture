"""Guide routes.

Purpose: serve the markdown pages in docs/ and one diagram from docs/assets.
Used by: agentic/01-entry/app.py. The Docs screen calls GET /guide.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Header, HTTPException
from fastapi.responses import FileResponse

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

_auth = load_module(
    Path(__file__).resolve().parents[2] / "02-guardrails" / "auth" / "auth.py",
    "agent_api_auth",
)


def mount(app, platform) -> None:

    @app.get("/guide", tags=["Guide"], summary="Markdown pages from docs/")
    def guide(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        pages = []
        for path in sorted((ROOT / "docs").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = path.stem.replace("-", " ").title()
            for line in text.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            pages.append({"id": path.stem, "title": title, "markdown": text})
        return pages

    @app.get("/guide/assets/{name}", tags=["Guide"], summary="One diagram from docs/assets")
    def guide_asset(name: str):
        path = asset_file(name)
        if path is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return FileResponse(path)


def asset_file(name: str):
    root = (ROOT / "docs" / "assets").resolve()
    path = (root / name).resolve()
    if path.parent != root or not path.is_file():
        return None
    return path
