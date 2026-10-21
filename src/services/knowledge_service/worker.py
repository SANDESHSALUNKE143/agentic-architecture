"""Durable PostgreSQL job processing with idempotent Qdrant writes."""

from __future__ import annotations

from agentic_sdk.contracts import Context, Document
from agentic_sdk.services.knowledge_service.components import components


def work_once(db, embedder, store):
    """A transaction owns each job through external upsert; crashed workers release the lock.
    Versioned document IDs make retries safe. New document versions use new IDs.
    """
    with db.connect() as connection:
        row = connection.execute(
            "SELECT * FROM ingestion_jobs WHERE state='pending' ORDER BY created FOR UPDATE SKIP LOCKED LIMIT 1"
        ).fetchone()
        if not row:
            return False
        ctx = Context(row["tenant"], row["agent"], frozenset({"index:admin", "knowledge:write"}))
        try:
            store.provision(ctx)
            # Content identity is used in the point ID so simultaneous versions cannot overwrite one another.
            doc = Document(row["document_id"] + "-" + row["fingerprint"][:16], row["content"])
            store.upsert(ctx, doc, embedder.embed(doc.text))
            connection.execute(
                "UPDATE ingestion_jobs SET state='complete',error=NULL WHERE id=%s",
                (row["id"],),
            )
        except Exception:
            connection.execute(
                "UPDATE ingestion_jobs SET state='failed',error='ingestion failed; inspect infrastructure' WHERE id=%s",
                (row["id"],),
            )
    return True


def worker():
    """Process queued ingestion jobs serially, sleeping briefly when the queue is empty.

    PostgreSQL transaction locks own each job; a process crash releases the lock.
    Failed jobs retain a sanitized error and are not automatically retried."""
    import time

    db, embedder, store = components()
    db.initialize()
    while True:
        if not work_once(db, embedder, store):
            time.sleep(1)


if __name__ == "__main__":
    worker()
