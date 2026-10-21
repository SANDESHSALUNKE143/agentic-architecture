"""
Tools for the insight agent.

Five allowlisted hands: metrics, past analyses, the city graph, the trend
model, and the public site. Each method calls one environment port. The
model sees the schema, not the connection.

Usage:
    tools = register(ports)
"""

from agentic_sdk.core.execution.tools import ToolRegistry, ToolSpec

# ── Schemas ───────────────────────────────────────────────────────────

_METRICS = {
    "type": "object",
    "properties": {
        "table": {"type": "string", "enum": ["city_metrics"]},
        "limit": {"type": "integer"},
    },
    "required": ["table", "limit"],
}
_ANALYSES = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "limit": {"type": "integer"},
    },
    "required": ["query", "limit"],
}
_GRAPH = {
    "type": "object",
    "properties": {"entity": {"type": "string"}},
    "required": ["entity"],
}
_TREND = {
    "type": "object",
    "properties": {
        "model_id": {"type": "string", "enum": ["city_trend"]},
        "features": {"type": "object"},
    },
    "required": ["model_id", "features"],
}
_SITE = {
    "type": "object",
    "properties": {
        "host": {"type": "string", "enum": ["stats.example"]},
        "path": {"type": "string"},
    },
    "required": ["host", "path"],
}

# ── Hands ─────────────────────────────────────────────────────────────


class _Hands:
    """The five tool handlers bound to one set of open ports."""

    def __init__(self, ports):
        """Keep the open ports and the SQL connection this process can replace."""
        self.ports = ports
        self.connection = ports.sql.connection

    async def query_metrics(self, ctx, arguments):
        """Read the allowlisted metrics table and finish the database transaction."""
        for attempt in (1, 2):
            try:
                result = self.ports.sql.query(ctx, arguments["table"], arguments["limit"])
            except Exception:
                self._reset_connection()
                if attempt == 2:
                    raise
                self.connection = self.ports.connect_sql()
                self.ports.sql.connection = self.connection
                continue
            self.connection.commit()
            return result

    def _reset_connection(self):
        """Roll back the failed transaction, or close it when rollback itself fails."""
        try:
            self.connection.rollback()
        except Exception:
            self.connection.close()

    async def search_analyses(self, ctx, arguments):
        """Embed the query with the SDK hash profile and search the Qdrant collection."""
        hits = self.ports.store.search(
            ctx, self.ports.embedder.embed(arguments["query"]), arguments["limit"]
        )
        return {
            "hits": [
                {"id": hit.document.id, "text": hit.document.text, "score": hit.score}
                for hit in hits
            ]
        }

    async def expand_graph(self, ctx, arguments):
        """Expand one entity through the SDK Neo4j adapter."""
        return self.ports.graph.expand(ctx, arguments["entity"])

    async def predict_trend(self, ctx, arguments):
        """Run the registered trend model."""
        return self.ports.models.predict(ctx, arguments["model_id"], arguments["features"])

    async def fetch_site(self, ctx, arguments):
        """Fetch one path on the allowlisted site."""
        return self.ports.web.fetch(ctx, arguments["host"], arguments["path"])

    def specs(self):
        """Return the five tool specifications in call order."""
        return (
            ToolSpec(
                "query_metrics",
                "Read city index rows from the allowlisted table.",
                "sql:read",
                _METRICS,
                self.query_metrics,
            ),
            ToolSpec(
                "search_analyses",
                "Search past written analyses.",
                "knowledge:read",
                _ANALYSES,
                self.search_analyses,
            ),
            ToolSpec(
                "expand_graph",
                "Expand one city in the graph.",
                "graph:read",
                _GRAPH,
                self.expand_graph,
            ),
            ToolSpec(
                "predict_trend",
                "Score a city with the registered trend model.",
                "model:invoke",
                _TREND,
                self.predict_trend,
            ),
            ToolSpec(
                "fetch_site",
                "Read a page from the allowlisted site.",
                "web:read",
                _SITE,
                self.fetch_site,
            ),
        )


def register(ports):
    """Add the five allowlisted tools and return the registry."""
    tools = ToolRegistry()
    for spec in _Hands(ports).specs():
        tools.add(spec)
    return tools
