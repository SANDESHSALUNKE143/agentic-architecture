"""
Read-only SQL port.

The agent opens the database connection and passes it in, with the table
allowlist. This adapter checks sql:read, the table name, and the row cap,
then runs a fixed SELECT. It does not accept SQL text or a connection string
from the model.

Usage:
    sql = ReadOnlySql(connection, tables=frozenset({"sample_rows"}), paramstyle="pyformat")
    rows = sql.query(context, "sample_rows", 5)
"""

import re

from agentic_sdk.contracts.orchestration.types import ExecutionError
from agentic_sdk.core.context.identity import Context

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


# ── Allowlisted read ──────────────────────────────────────────────────


class ReadOnlySql:
    """SELECT from allowlisted tables only. No model-supplied SQL or connection string."""

    def __init__(
        self,
        connection,
        *,
        tables: frozenset[str],
        row_cap: int = 20,
        timeout_ms: int = 5000,
        paramstyle: str = "qmark",
    ):
        """Bind a DB-API connection, an identifier allowlist, a row cap and a timeout.

        paramstyle is qmark for SQLite tests and pyformat for PostgreSQL. The timeout
        is applied as SET LOCAL statement_timeout only for pyformat connections."""
        if type(row_cap) is not int or not 1 <= row_cap <= 100:
            raise ValueError("row cap must be 1..100")
        if type(timeout_ms) is not int or not 1 <= timeout_ms <= 60000:
            raise ValueError("timeout must be 1..60000 ms")
        if paramstyle not in {"qmark", "pyformat"}:
            raise ValueError("unsupported paramstyle")
        if not tables or any(not _NAME.fullmatch(name) for name in tables):
            raise ValueError("allowlist must be simple table names")
        self.connection = connection
        self.tables = frozenset(tables)
        self.row_cap = row_cap
        self.timeout_ms = timeout_ms
        self.paramstyle = paramstyle

    def query(self, ctx: Context, table: str, limit: int) -> dict:
        """Require sql:read and return at most the row cap from one allowlisted table."""
        ctx.require("sql:read")
        if table not in self.tables:
            raise ExecutionError("table is not allowlisted")
        if type(limit) is not int or not 1 <= limit <= self.row_cap:
            raise ExecutionError("limit exceeds row cap")
        if self.paramstyle == "pyformat":
            self.connection.execute(f"SET LOCAL statement_timeout = {self.timeout_ms}")
            placeholder = "%s"
        else:
            placeholder = "?"
        cursor = self.connection.execute(
            f"SELECT * FROM {table} LIMIT {placeholder}",
            (limit,),
        )
        columns = [column[0] for column in cursor.description]
        rows = [_materialize(raw, columns) for raw in cursor.fetchall()]
        return {"table": table, "rows": rows}


def _materialize(raw, columns: list[str]) -> dict:
    """Copy one DB-API row into a plain dict without keeping the driver object."""
    if isinstance(raw, dict):
        return {key: raw[key] for key in raw}
    if hasattr(raw, "keys"):
        return {key: raw[key] for key in raw.keys()}
    return dict(zip(columns, raw))
