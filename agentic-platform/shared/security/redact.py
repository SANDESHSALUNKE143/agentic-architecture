"""Drop secrets and instruction-like lines from traces and retrieved text."""

from __future__ import annotations

import json
from typing import Any

SECRET_PARTS = ("token", "password", "secret", "authorization", "api_key", "apikey")
OMIT_KEYS = {"text", "passage", "body", "document", "content"}
INJECTION_MARKS = (
    "ignore previous",
    "ignore all previous",
    "grant permission",
    "you are now",
    "system prompt",
    "bypass approval",
)


def _secret_key(key: str) -> bool:
    lowered = key.lower().replace("-", "_")
    return any(part in lowered for part in SECRET_PARTS)


def summarize(value: Any, limit: int = 240) -> str:
    """Short JSON summary. Secret fields and document bodies never appear."""
    cleaned = _clean(value)
    text = cleaned if isinstance(cleaned, str) else json.dumps(cleaned, default=str)
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if _secret_key(str(key)):
                out[str(key)] = "[redacted]"
            elif str(key) in OMIT_KEYS:
                out[str(key)] = "[omitted]"
            else:
                out[str(key)] = _clean(item)
        return out
    if isinstance(value, list):
        return [_clean(item) for item in value[:12]]
    if isinstance(value, str):
        return value[:180]
    return value


def strip_untrusted(text: str) -> str:
    """Remove lines that try to override tool policy. The rest of the text stays."""
    kept = []
    for line in str(text).splitlines():
        lowered = line.lower()
        if any(mark in lowered for mark in INJECTION_MARKS):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def contains_injection(text: str) -> bool:
    lowered = str(text).lower()
    return any(mark in lowered for mark in INJECTION_MARKS)
