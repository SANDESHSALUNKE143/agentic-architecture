"""One-hop Neo4j expansion. The Cypher text is fixed inside this adapter."""

from agentic_sdk.contracts.orchestration.types import ExecutionError
from agentic_sdk.core.context.identity import Context

_CYPHER = """
MATCH (n {name: $entity})-[r]->(m)
RETURN type(r) AS relation, m.name AS target, m.passage AS passage
LIMIT $limit
"""


class Neo4jGraphRag:
    """Expand one named entity through an operator-supplied Neo4j session."""

    def __init__(self, session, *, max_neighbors: int = 8):
        """Keep a session-like object with run(cypher, **parameters). Cap neighbors at 8."""
        if type(max_neighbors) is not int or not 1 <= max_neighbors <= 8:
            raise ValueError("max neighbors must be 1..8")
        self.session = session
        self.max_neighbors = max_neighbors

    def expand(self, ctx: Context, entity: str) -> dict:
        """Require graph:read and return at most max_neighbors plus up to four passages."""
        ctx.require("graph:read")
        if not isinstance(entity, str) or not entity.strip() or len(entity) > 200:
            raise ExecutionError("entity is required")
        records = self.session.run(_CYPHER, entity=entity, limit=self.max_neighbors)
        neighbors = []
        passages = []
        for record in records:
            if len(neighbors) >= self.max_neighbors:
                break
            neighbors.append({"relation": record["relation"], "target": record["target"]})
            passage = record["passage"]
            if passage and passage not in passages and len(passages) < 4:
                passages.append(passage)
        return {"entity": entity, "neighbors": neighbors, "passages": passages}
