"""Scoped ingestion-job submission, status lookup and vector retrieval endpoints."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import asdict

from agentic_sdk.services.contracts import Ingestion, Search
from fastapi import Header, HTTPException


def register(app, db, embedder, store, auth, observer):
    """Register bounded submission, scoped job-status and retrieval routes over injected adapters."""

    @app.post("/v1/knowledge/documents", status_code=202)
    def ingest(body: Ingestion, authorization: str | None = Header(default=None)):
        """Queue an idempotent content/profile version, applying per-scope pending-job backpressure."""
        ctx = auth(authorization, "knowledge:write")
        if len(body.text.encode()) > 16000:
            raise HTTPException(422, "document exceeds byte limit")
        fingerprint = hashlib.sha256(
            (embedder.profile.fingerprint + body.text).encode()
        ).hexdigest()
        with db.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                ("ingestion:" + ctx.tenant_id + ":" + ctx.agent_id,),
            )
            pending = connection.execute(
                "SELECT count(*) AS total FROM ingestion_jobs WHERE tenant=%s AND agent=%s AND state='pending'",
                (ctx.tenant_id, ctx.agent_id),
            ).fetchone()["total"]
            if pending >= 1000:
                raise HTTPException(429, "ingestion queue capacity reached")
            row = connection.execute(
                """INSERT INTO ingestion_jobs(id,tenant,agent,document_id,content,fingerprint)
                VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(tenant,agent,document_id,fingerprint)
                DO UPDATE SET fingerprint=EXCLUDED.fingerprint RETURNING id,state""",
                (
                    uuid.uuid4().hex,
                    ctx.tenant_id,
                    ctx.agent_id,
                    body.document_id,
                    body.text,
                    fingerprint,
                ),
            ).fetchone()
        return row

    @app.get("/v1/knowledge/jobs/{job_id}")
    def job(job_id: str, authorization: str | None = Header(default=None)):
        """Read job state without exposing document content; other scopes receive 404."""
        ctx = auth(authorization, "knowledge:read")
        with db.connect() as connection:
            row = connection.execute(
                "SELECT id,state,error FROM ingestion_jobs WHERE id=%s AND tenant=%s AND agent=%s",
                (job_id, ctx.tenant_id, ctx.agent_id),
            ).fetchone()
        if not row:
            raise HTTPException(404, "job not found")
        return row

    @app.post("/v1/knowledge/search")
    def search(body: Search, authorization: str | None = Header(default=None)):
        """Retrieve only the credential scope and current embedding profile; an absent index is empty."""
        ctx = auth(authorization, "knowledge:read")
        if not store.client.collection_exists(store.collection(ctx)):
            return {"hits": [], "profile": embedder.profile.fingerprint}
        hits = store.search(ctx, embedder.embed(body.question), body.limit)
        observer.emit(
            ctx,
            uuid.uuid4().hex,
            "knowledge.search",
            {"status": "ok", "steps": len(hits)},
        )
        return {
            "hits": [asdict(h) for h in hits],
            "profile": embedder.profile.fingerprint,
        }
