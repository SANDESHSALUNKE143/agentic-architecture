"""Settings and memory routes.

Purpose: read and save one contract, and save a connector without returning its password.
Used by: apps/agent-api/app.py. Configuration, the gear, and connectors call these routes.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Header, HTTPException
from fastapi.responses import FileResponse
from shared.config import ROOT
from shared.loader import load_module

_HERE = Path(__file__).resolve().parent
_bodies = load_module(_HERE / "bodies.py", "agent_api_bodies")
_auth = load_module(_HERE / "auth.py", "agent_api_auth")
_view = load_module(_HERE / "contract_view.py", "agent_api_contract_view")


def mount(app, platform) -> None:
    @app.get("/settings/platform", tags=["Settings"], summary="Mode, limits, and which hosts are configured")
    def platform_settings(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return platform.platform_settings()

    @app.get("/settings/agents/{agent_id}", tags=["Settings"], summary="One agent contract")
    def agent_settings(agent_id: str, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        contract = platform.contracts.get(agent_id)
        if contract is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return _view.contract_view(contract)

    @app.put("/settings/agents/{agent_id}", tags=["Settings"], summary="Save one agent contract")
    def save_agent_settings(agent_id: str, body: _bodies.ContractBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        if agent_id not in platform.contracts:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            contract = platform.update_contract(agent_id, body.model_dump(exclude_none=True))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return _view.contract_view(contract)

    @app.get("/settings/agents/{agent_id}/file", tags=["Settings"], summary="Download the agent YAML")
    def agent_file(agent_id: str, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        contract = platform.contracts.get(agent_id)
        if contract is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        path = Path(contract.path).resolve()
        root = (ROOT / "agents").resolve()
        if root not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="Agent file not found")
        return FileResponse(path, media_type="text/yaml", filename=f"{agent_id}.yaml")

    @app.get("/settings/connections", tags=["Settings"], summary="Connector addresses, without passwords")
    def connections(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return platform.endpoints()

    @app.put("/settings/connections/{endpoint_id}", tags=["Settings"], summary="Save one connector address")
    def save_connection(endpoint_id: str, body: _bodies.EndpointBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        try:
            return platform.save_endpoint(endpoint_id, body.url, body.connection_string, body.username, body.password)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/memory/notes", tags=["Memory"], summary="Store a short note for one user")
    def add_note(body: _bodies.NoteBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return platform.memory.add_note(body.user_id, body.text)
