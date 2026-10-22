"""Process settings. Defaults run the local mock."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_TOKEN = "local-dev-token-not-for-production"


def setting(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def platform_env() -> str:
    return setting("PLATFORM_ENV", "development")


def dev_token() -> str:
    return setting("PLATFORM_DEV_TOKEN", DEV_TOKEN)


def assert_runtime_config() -> None:
    if platform_env() == "production" and dev_token() == DEV_TOKEN:
        raise RuntimeError(
            "PLATFORM_ENV=production rejects the default PLATFORM_DEV_TOKEN. Set a private token."
        )


def data_dir() -> Path:
    raw = setting("PLATFORM_DATA_DIR", "")
    path = Path(raw) if raw else ROOT / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def llm_mode() -> str:
    return setting("PLATFORM_LLM_MODE", "mock")


MAX_HOPS = 6
MAX_TOOLS = int(setting("PLATFORM_MAX_TOOLS", "12") or "12")
TIMEOUT_SECONDS = float(setting("PLATFORM_TIMEOUT_SECONDS", "8") or "8")
MAX_TASK_CHARS = 4000
MAX_OUTPUT_CHARS = 8000
