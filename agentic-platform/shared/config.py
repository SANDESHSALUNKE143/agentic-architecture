"""Environment settings. Defaults are enough to run the local mock."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_TOKEN = "local-dev-token-not-for-production"


def setting(name: str, default: str = "") -> str:
    """Return an environment variable or the given default."""
    return os.environ.get(name, default)


def platform_env() -> str:
    """development or production. Production rejects the fixed dev token."""
    return setting("PLATFORM_ENV", "development")


def dev_token() -> str:
    """Bearer token for the local API."""
    return setting("PLATFORM_DEV_TOKEN", DEV_TOKEN)


def assert_runtime_config() -> None:
    """Fail startup when production still uses the published dev token."""
    if platform_env() == "production" and dev_token() == DEV_TOKEN:
        raise RuntimeError(
            "PLATFORM_ENV=production rejects PLATFORM_DEV_TOKEN default. "
            "Set PLATFORM_DEV_TOKEN to a private value."
        )


def data_dir() -> Path:
    """Directory for notes and learned examples. Override with PLATFORM_DATA_DIR."""
    raw = setting("PLATFORM_DATA_DIR", "")
    path = Path(raw) if raw else ROOT / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def llm_mode() -> str:
    """mock unless PLATFORM_LLM_MODE=live and MODEL_API_KEY is set."""
    return setting("PLATFORM_LLM_MODE", "mock")


MAX_HOPS = 6
MAX_TOOLS = 12
TIMEOUT_SECONDS = float(setting("PLATFORM_TIMEOUT_SECONDS", "8") or "8")
MAX_TASK_CHARS = 4000
MAX_OUTPUT_CHARS = 8000
