"""Allowlisted web fetch. The model may pick a known host and a relative path."""

import json
import urllib.request

from agentic_sdk.contracts.orchestration.types import ExecutionError
from agentic_sdk.core.context.identity import Context


class AllowlistedWeb:
    """Fetch JSON from operator-configured origins. Unknown hosts never leave the process."""

    def __init__(self, bases: dict[str, str], *, timeout: float = 5, opener=None):
        """Map each public host name to an operator origin. opener replaces urllib in tests."""
        if not bases or any("://" in host or not host for host in bases):
            raise ValueError("hosts must be bare names")
        if any(not origin.startswith("http") for origin in bases.values()):
            raise ValueError("origins must be absolute http(s) URLs")
        self.bases = dict(bases)
        self.timeout = timeout
        self.opener = opener

    def fetch(self, ctx: Context, host: str, path: str) -> dict:
        """Require web:read, reject unknown hosts and unsafe paths, and return a JSON object."""
        ctx.require("web:read")
        if host not in self.bases:
            raise ExecutionError("host is not allowlisted")
        if (
            not isinstance(path, str)
            or not path.startswith("/")
            or path.startswith("//")
            or "://" in path
            or ".." in path
            or "?" in path
            or "#" in path
        ):
            raise ExecutionError("path must be a relative path")
        url = self.bases[host].rstrip("/") + path
        if self.opener is not None:
            body = self.opener(url)
        else:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                body = json.loads(response.read(250_000))
        if not isinstance(body, dict):
            raise ExecutionError("web response must be an object")
        return {"host": host, "path": path, "body": body}
