"""
auth.py — Clerk JWT verification for ChefSnap FastAPI backend.

Provides get_optional_user_id: a FastAPI dependency that returns the Clerk
user ID (str) if a valid Bearer token is present, or None for unauthenticated
requests (guest usage is always allowed — guests get IP-based rate limiting).

CLERK_JWKS_URL must be set in production to the frontend-API JWKS endpoint:
  https://<your-clerk-frontend-api>/.well-known/jwks.json
If unset (local dev), JWTs are decoded without signature verification so the
dev experience is uninterrupted.
"""

import os
import time
import logging
from typing import Optional

import httpx
from fastapi import Request
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

CLERK_JWKS_URL: str = os.getenv("CLERK_JWKS_URL", "")
_ALGORITHMS = ["RS256"]

# (keys_dict, fetched_at) — refreshed every hour
_jwks_cache: tuple[dict, float] | None = None
_JWKS_TTL = 3600.0


def _fetch_jwks() -> dict:
    global _jwks_cache
    now = time.time()
    if _jwks_cache and now - _jwks_cache[1] < _JWKS_TTL:
        return _jwks_cache[0]
    try:
        resp = httpx.get(CLERK_JWKS_URL, timeout=5.0)
        resp.raise_for_status()
        keys = resp.json()
        _jwks_cache = (keys, now)
        return keys
    except Exception as exc:
        logger.warning("JWKS fetch failed: %s", exc)
        if _jwks_cache:
            return _jwks_cache[0]  # serve stale rather than block all requests
        raise


def _bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    return auth[7:] if auth.startswith("Bearer ") else None


async def get_optional_user_id(request: Request) -> Optional[str]:
    """
    FastAPI dependency — never raises.
    Returns Clerk user_id (str) or None (unauthenticated / invalid token).
    """
    token = _bearer_token(request)
    if not token:
        return None

    if not CLERK_JWKS_URL:
        # Dev mode: decode without signature verification
        try:
            return jwt.get_unverified_claims(token).get("sub")
        except Exception:
            return None

    try:
        jwks = _fetch_jwks()
        payload = jwt.decode(token, jwks, algorithms=_ALGORITHMS)
        return payload.get("sub")
    except (JWTError, Exception) as exc:
        logger.debug("Token verification failed: %s", exc)
        return None
