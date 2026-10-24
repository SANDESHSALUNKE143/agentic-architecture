"""Bearer check.

Purpose: compare Authorization to the process token. Guide images do not call this.
Used by: every route module in this folder.
"""

from __future__ import annotations

import secrets

from fastapi import HTTPException
from shared.config import dev_token


def authorized(authorization: str | None) -> None:
    expected = f"Bearer {dev_token()}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")
