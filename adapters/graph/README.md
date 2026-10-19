# Graph RAG adapter

Neo4j one-hop expansion. Cypher is fixed in this module. Agents pass an entity name.

## Current status

Implemented against any session object that accepts run(cypher, entity=, limit=). The prototype wires the official Neo4j driver.

## Where to work

[Neo4j implementation](neo4j.py).

[Parent section](../README.md) · [Graph contract](../../contracts/graph/README.md)

## Folder contents

- [neo4j.py](neo4j.py): Bounded neighborhood and passage expansion.
