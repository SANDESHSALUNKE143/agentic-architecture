"""Request guard.

Purpose: rate limit every call, reject an oversized body, and hide unexpected errors.
Used by: apps/agent-api/app.py. Authentication stays in auth.py.
"""

from __future__ import annotations

import hashlib
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.config import setting
from shared.security.rate_limit import SlidingWindow

logger = logging.getLogger("agentic.api")
limiter = SlidingWindow()
_MAX_BODY = 262_144


def install(app: FastAPI) -> None:
    app.add_exception_handler(Exception, unhandled)
    app.middleware("http")(protect)


async def protect(request: Request, call_next):
    if _too_large(request.headers.get("content-length")):
        return _secure(_json(413, "Request body is too large."))
    allowed, retry = limiter.allow(_key(request), _limit(), _window())
    if not allowed:
        response = _json(429, "Too many requests.")
        response.headers["Retry-After"] = str(retry)
        return _secure(response)
    response = await call_next(request)
    return _secure(response)


async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("request failed: %s", type(exc).__name__)
    return _secure(_json(500, "The server could not complete the request."))


def _too_large(header: str | None) -> bool:
    if not header:
        return False
    try:
        length = int(header)
    except ValueError:
        return False
    return length > int(setting("PLATFORM_MAX_BODY", str(_MAX_BODY)) or _MAX_BODY)


def _limit() -> int:
    try:
        return max(1, int(setting("PLATFORM_RATE_LIMIT", "120") or "120"))
    except ValueError:
        return 120


def _window() -> float:
    try:
        return max(1.0, float(setting("PLATFORM_RATE_WINDOW", "60") or "60"))
    except ValueError:
        return 60.0


def _key(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    token = request.headers.get("authorization") or ""
    digest = hashlib.sha256(token.encode()).hexdigest()[:16]
    return f"{host}|{digest}"


def _json(status: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail})


def _secure(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response
