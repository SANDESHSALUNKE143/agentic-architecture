"""HTTP API. The body becomes an AgentRequest. The response is an AgentResponse."""

from __future__ import annotations

import json
import secrets

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from orchestrator.platform import Platform
from pydantic import BaseModel, Field
from shared.config import ROOT, assert_runtime_config, dev_token
from shared.contracts import AgentRequest

assert_runtime_config()
platform = Platform()
app = FastAPI(title="Agentic architecture")


class RunBody(BaseModel):
    task: str
    user_id: str = "local-development-user"
    session_id: str = ""
    workflow: str | None = None
    agents: list[str] | None = None


class DecisionBody(BaseModel):
    decision: str
    actor: str = "local-operator"


class FeedbackBody(BaseModel):
    helpful: bool
    note: str = ""


class ContractBody(BaseModel):
    instructions: list[str] | None = None
    tools: list[str] | None = None
    memory: dict | None = None
    approval: dict | None = None
    permissions: dict | None = None


class NoteBody(BaseModel):
    user_id: str
    text: str = Field(max_length=500)


def _authorized(authorization: str | None) -> None:
    expected = f"Bearer {dev_token()}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health(authorization: str | None = Header(default=None)):
    _authorized(authorization)
    return platform.health()


@app.get("/agents")
def agents(authorization: str | None = Header(default=None)):
    _authorized(authorization)
    return [
        {"name": contract.name, "description": contract.description, "tools": contract.tools}
        for contract in platform.contracts.values()
    ]


@app.get("/tools")
def tools(authorization: str | None = Header(default=None)):
    _authorized(authorization)
    return platform.gateway.describe()


@app.post("/agent-runs")
def start_run(body: RunBody, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    request = AgentRequest(
        task=body.task,
        user_id=body.user_id,
        session_id=body.session_id,
        workflow=body.workflow,
        agents=body.agents,
    )
    return platform.start(request)


@app.post("/agent-runs/stream")
async def stream_run(body: RunBody, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    request = AgentRequest(
        task=body.task,
        user_id=body.user_id,
        session_id=body.session_id,
        workflow=body.workflow,
        agents=body.agents,
    )

    async def events():
        import asyncio

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def emit(payload: dict) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, payload)

        def work() -> None:
            try:
                result = platform.start(request, on_event=emit)
                emit({"type": "done", "run": result})
            except Exception as exc:
                emit({"type": "error", "message": str(exc)})
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        loop.run_in_executor(None, work)
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
            await asyncio.sleep(0.12)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/agent-runs/{run_id}")
def get_run(run_id: str, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    run = platform.store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return platform.public_run(run)


@app.post("/agent-runs/{run_id}/cancel")
def cancel_run(run_id: str, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    if not platform.store.cancel(run_id):
        raise HTTPException(status_code=409, detail="Run is not running")
    return {"status": "cancelling"}


@app.post("/agent-runs/{run_id}/feedback")
def feedback(run_id: str, body: FeedbackBody, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    platform.evaluation.add_feedback(run_id, body.helpful, body.note)
    return {"status": "recorded"}


@app.get("/plugins")
def plugins(authorization: str | None = Header(default=None)):
    _authorized(authorization)
    return platform.plugins()


class PluginBody(BaseModel):
    agents: list[str]


@app.put("/plugins/{name}")
def connect_plugin(name: str, body: PluginBody, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    try:
        return platform.connect_plugin(name, body.agents)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/guide")
def guide(authorization: str | None = Header(default=None)):
    _authorized(authorization)
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


@app.get("/guide/assets/{name}")
def guide_asset(name: str):
    path = (ROOT / "docs" / "assets" / name).resolve()
    root = (ROOT / "docs" / "assets").resolve()
    if path.parent != root or not path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(path)


@app.get("/approvals")
def approvals(authorization: str | None = Header(default=None)):
    _authorized(authorization)
    return list(platform.store.approvals.values())


@app.post("/approvals/{approval_id}/decision")
def decide(approval_id: str, body: DecisionBody, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    run, error = platform.resume(approval_id, body.decision, body.actor)
    if error == "self_approval":
        raise HTTPException(status_code=403, detail="The actor cannot approve their own agent")
    if error:
        raise HTTPException(status_code=409, detail=error)
    return run


@app.get("/settings/platform")
def platform_settings(authorization: str | None = Header(default=None)):
    _authorized(authorization)
    return platform.platform_settings()


@app.get("/settings/agents/{agent_id}")
def agent_settings(agent_id: str, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    contract = platform.contracts.get(agent_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _contract_view(contract)


@app.put("/settings/agents/{agent_id}")
def save_agent_settings(agent_id: str, body: ContractBody, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    if agent_id not in platform.contracts:
        raise HTTPException(status_code=404, detail="Agent not found")
    updates = body.model_dump(exclude_none=True)
    try:
        contract = platform.update_contract(agent_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _contract_view(contract)


@app.post("/memory/notes")
def add_note(body: NoteBody, authorization: str | None = Header(default=None)):
    _authorized(authorization)
    return platform.memory.add_note(body.user_id, body.text)


def _contract_view(contract) -> dict:
    return {
        "name": contract.name,
        "description": contract.description,
        "instructions": contract.instructions,
        "tools": contract.tools,
        "memory": contract.memory,
        "permissions": contract.permissions,
        "approval": contract.approval,
        "output_schema": contract.output_schema,
    }
