"""Offline retrieval smoke evaluation, not an LLM quality benchmark."""

from agentic_sdk.adapters.local import HashEmbedder, MemoryStore
from agentic_sdk.contracts import Context, Document

e = HashEmbedder()
s = MemoryStore(e.profile)
c = Context("eval", "retrieval", frozenset({"knowledge:write", "knowledge:read"}))
corpus = [
    ("sdk", "sdk adapters reusable package"),
    ("cost", "budget tokens cost quotas"),
    ("index", "embedding vectors index compatibility"),
]
for id, text in corpus:
    s.upsert(c, Document(id, text), e.embed(text))
passed = sum(
    s.search(c, e.embed(query), 1)[0].document.id == expected
    for expected, query in [
        ("sdk", "sdk adapters"),
        ("cost", "tokens budget"),
        ("index", "embedding vectors"),
    ]
)
print(f"retrieval recall@1: {passed}/3")
assert passed == 3
