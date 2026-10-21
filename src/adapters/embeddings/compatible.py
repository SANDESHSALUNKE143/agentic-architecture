"""Compatible embeddings endpoint adapter with strict profile validation."""

from agentic_sdk.contracts import EmbeddingProfile, validate_vector


class CompatibleEmbedder:
    """Map a compatible embeddings endpoint to one declared embedding profile."""

    def __init__(self, client, deployment: str, profile: EmbeddingProfile):
        self.client, self.deployment, self.profile = client, deployment, profile

    def embed(self, text: str) -> list[float]:
        """Request a vector and validate its dimensions and normalization against the profile."""
        result = self.client.embeddings.create(model=self.deployment, input=[text])
        return validate_vector(result.data[0].embedding, self.profile)
