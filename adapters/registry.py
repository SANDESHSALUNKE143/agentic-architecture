"""Explicit registration; configuration never imports arbitrary code."""

from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """Explicit name-to-factory registry; configuration never imports arbitrary Python code."""

    def __init__(self):
        self._factories: dict[str, Callable[..., T]] = {}

    def register(self, name: str, factory: Callable[..., T]) -> None:
        """Register one unique adapter name; replacing an existing factory is rejected."""
        if name in self._factories:
            raise ValueError("duplicate adapter: " + name)
        self._factories[name] = factory

    def create(self, name: str, **options) -> T:
        """Call an already registered factory with options; reject unknown adapter names."""
        if name not in self._factories:
            raise ValueError("unknown adapter: " + name)
        return self._factories[name](**options)
