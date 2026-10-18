"""Embedding profiles, vector validation and embedder contract."""

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmbeddingProfile:
    """Immutable identity of an embedding/index representation.

    Model revision, dimensions, normalization, distance and preprocessing all affect
    compatibility. Equal dimensions alone do not make two indexes interchangeable."""

    model: str
    revision: str
    dimensions: int
    normalization: str = "l2"
    distance: str = "cosine"
    preprocessing: str = "plain-v1"

    def __post_init__(self):
        if self.dimensions < 1 or self.normalization != "l2" or self.distance != "cosine":
            raise ValueError("v0.1 supports positive dimensions, l2, cosine only")

    @property
    def fingerprint(self) -> str:
        """Return a deterministic SHA-256 identifier for the entire profile."""
        return hashlib.sha256(json.dumps(self.__dict__, sort_keys=True).encode()).hexdigest()


def validate_vector(vector: list[float], profile: EmbeddingProfile) -> list[float]:
    """Reject nonfinite, zero or dimension-mismatched vectors and return L2-normalized values."""
    if len(vector) != profile.dimensions or not all(math.isfinite(x) for x in vector):
        raise ValueError("invalid embedding dimensions or values")
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        raise ValueError("zero vector")
    return [x / norm for x in vector]


class Embedder(Protocol):
    """Embedding port exposing the exact profile used to produce its vectors."""

    profile: EmbeddingProfile

    def embed(self, text: str) -> list[float]:
        """Return one vector compatible with profile; adapters validate dimension and normalization."""
        ...
