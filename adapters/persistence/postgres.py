"""PostgreSQL persistence and atomic scope/day token reservations."""

from __future__ import annotations

from fastapi import HTTPException


class Database:
    """PostgreSQL persistence for immutable configurations, ingestion jobs and token reservations.

    Each connect call owns a short-lived connection. SQL context managers commit
    on success and roll back on exceptions. Schema creation is prototype bootstrap,
    not a general migration framework."""

    def __init__(self, dsn):
        self.dsn = dsn

    def connect(self):
        """Create a dict-row psycopg connection with a five-second connection deadline.

        The caller owns closing and transaction completion via a context manager."""
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5)

    def initialize(self):
        """Create missing prototype tables idempotently; do not alter existing schema versions."""
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS configurations (
                tenant TEXT NOT NULL, agent TEXT NOT NULL, revision INTEGER NOT NULL,
                config JSONB NOT NULL, PRIMARY KEY(tenant,agent,revision))""")
            db.execute("""CREATE TABLE IF NOT EXISTS ingestion_jobs (
                id TEXT PRIMARY KEY, tenant TEXT NOT NULL, agent TEXT NOT NULL,
                document_id TEXT NOT NULL, content TEXT NOT NULL, fingerprint TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'pending', error TEXT,
                created TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE(tenant,agent,document_id,fingerprint))""")
            db.execute("""CREATE TABLE IF NOT EXISTS token_ledger (
                tenant TEXT NOT NULL, agent TEXT NOT NULL, day DATE NOT NULL DEFAULT CURRENT_DATE,
                reserved BIGINT NOT NULL DEFAULT 0, input_tokens BIGINT NOT NULL DEFAULT 0,
                output_tokens BIGINT NOT NULL DEFAULT 0, calls BIGINT NOT NULL DEFAULT 0,
                PRIMARY KEY(tenant,agent,day))""")

    def reserve(self, ctx, amount, daily_limit):
        """Atomically reserve daily tokens for a scope, or raise HTTP 429 if the cap would be exceeded.

        No refunds are applied to failed or ambiguous model calls. This is token
        admission control, not currency settlement."""
        with self.connect() as db:
            db.execute(
                "INSERT INTO token_ledger(tenant,agent) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                (ctx.tenant_id, ctx.agent_id),
            )
            row = db.execute(
                """UPDATE token_ledger SET reserved=reserved+%s,calls=calls+1
                WHERE tenant=%s AND agent=%s AND day=CURRENT_DATE AND reserved+%s<=%s RETURNING reserved""",
                (amount, ctx.tenant_id, ctx.agent_id, amount, daily_limit),
            ).fetchone()
            if not row:
                raise HTTPException(429, "daily token reservation exhausted")

    def usage(self, ctx, inp, out):
        """Add reported input/output usage to the current-day scoped reservation row."""
        with self.connect() as db:
            db.execute(
                """UPDATE token_ledger SET input_tokens=input_tokens+%s, output_tokens=output_tokens+%s
                WHERE tenant=%s AND agent=%s AND day=CURRENT_DATE""",
                (inp, out, ctx.tenant_id, ctx.agent_id),
            )
