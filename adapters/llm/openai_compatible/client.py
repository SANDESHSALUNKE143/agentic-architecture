"""Validated compatible-provider client construction and credential resolution."""

import os
from urllib.parse import urlparse


def client(base_url: str, api_key_env: str, allow_local_http: bool = False):
    """Create an OpenAI-compatible client with validated endpoint, environment key and no retries.

    The client has a 20-second provider timeout; callers own its lifecycle.
    Only explicitly enabled loopback endpoints may use HTTP."""
    from openai import OpenAI

    parsed = urlparse(base_url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("endpoint must not contain credentials, query or fragment")
    if parsed.scheme != "https" and not (
        allow_local_http
        and parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1"}
    ):
        raise ValueError("HTTPS required except explicitly enabled loopback")
    return OpenAI(base_url=base_url, api_key=os.environ[api_key_env], timeout=20, max_retries=0)
