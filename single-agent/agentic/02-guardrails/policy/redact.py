"""Strip untrusted instruction text.

Purpose: remove lines that try to override the contract, and drop secret-shaped values, before the model or a citation sees them.
Used by: the runtime and the document search port.
"""

from __future__ import annotations

import re

_SECRET = re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S+")
_INJECTION = re.compile(r"(?i)\b(ignore previous instructions|you are now|system:)\b.*?(\.|$)")


def strip_untrusted(text: str) -> str:
    kept = []
    for line in str(text).splitlines():
        cleaned = _SECRET.sub(r"\1=[redacted]", _INJECTION.sub("", line)).strip()
        if cleaned:
            kept.append(cleaned)
    return "\n".join(kept).strip()


def summarize(value: object) -> str:
    text = strip_untrusted(str(value))
    return text[:240]
