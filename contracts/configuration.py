"""Provider-neutral contract for versioned configuration sources."""

from typing import Mapping, Protocol


class ConfigSource(Protocol):
    """Port for loading a specific agent configuration revision from an approved source."""

    def load(self, agent_id: str, revision: str) -> Mapping[str, object]:
        """Return configuration for the requested agent and revision; implementations enforce authorization."""
        ...
