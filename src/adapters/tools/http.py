"""Reusable async REST transport. Tokens are injected, never inferred from arguments."""

import uuid
from urllib.parse import urlsplit


class RemoteError(RuntimeError):
    """Sanitized transport failure exposing a status and stable code, not upstream content."""

    def __init__(self, status: int, code: str):
        self.status, self.code = status, code
        super().__init__(f"remote request failed ({status}, {code})")


class JsonTransport:
    """Bounded, authenticated JSON transport for fixed paths on an approved endpoint.

    Redirects and automatic retries are disabled. HTTPS is the default; explicit
    loopback or operator-configured Docker hosts may allow HTTP. The caller owns
    closing the client. URL syntax validation is not a complete SSRF defense."""

    def __init__(
        self,
        base_url: str,
        token_provider,
        *,
        timeout: float = 20,
        allow_loopback_http: bool = False,
        transport=None,
        trusted_http_hosts: frozenset[str] = frozenset(),
        max_response_bytes: int = 250000,
    ):
        import httpx

        u = urlsplit(base_url)
        if not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError("invalid base URL")
        if (
            u.scheme != "https"
            and not (u.scheme == "http" and u.hostname in trusted_http_hosts)
            and not (
                allow_loopback_http
                and u.scheme == "http"
                and u.hostname in {"localhost", "127.0.0.1", "::1"}
            )
        ):
            raise ValueError("HTTPS required; only explicit loopback HTTP allowed")
        self.token_provider = token_provider
        self.max_response_bytes = max_response_bytes
        self.client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            trust_env=False,
        )

    async def request(self, method: str, path: str, *, body=None, params=None):
        """Inject a fresh bearer token and request ID, enforce response size and return a JSON object.

        Reject unsafe paths before I/O. Upstream errors, invalid JSON and transport
        failures become sanitized RemoteError exceptions. Mutations are never retried."""
        if (
            not path.startswith("/")
            or path.startswith("//")
            or "?" in path
            or "#" in path
            or ".." in path
            or "\\" in path
        ):
            raise ValueError("only fixed relative API paths are allowed")
        token = self.token_provider()
        if not isinstance(token, str) or not token or "\r" in token or "\n" in token:
            raise ValueError("missing or invalid access token")
        headers = {"Authorization": "Bearer " + token, "X-Request-Id": uuid.uuid4().hex}
        # No transparent retries: a POST can trigger an external mutation.
        try:
            async with self.client.stream(
                method, path.lstrip("/"), json=body, params=params, headers=headers
            ) as response:
                if response.status_code >= 300:
                    raise RemoteError(response.status_code, "UPSTREAM_REJECTED")
                content = bytearray()
                async for part in response.aiter_bytes():
                    content.extend(part)
                    if len(content) > self.max_response_bytes:
                        raise RemoteError(502, "RESPONSE_TOO_LARGE")
                import json

                result = json.loads(content)
                if not isinstance(result, dict):
                    raise RemoteError(502, "INVALID_RESPONSE")
                return result
        except RemoteError:
            raise
        except Exception as exc:
            raise RemoteError(502, "TRANSPORT_FAILURE") from exc

    async def aclose(self):
        """Close the owned async HTTP client and release its connections."""
        await self.client.aclose()
