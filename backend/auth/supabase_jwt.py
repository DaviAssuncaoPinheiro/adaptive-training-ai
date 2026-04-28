"""FastAPI dependency that validates Supabase access tokens.

Supabase projects may use either HS256 (symmetric) or ES256 (asymmetric) JWTs.
This module auto-detects the algorithm:
  - ES256: fetches the public key from the Supabase JWKS endpoint.
  - HS256: uses the SUPABASE_JWT_SECRET env var directly.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache

import jwt as pyjwt
from jwt import PyJWKClient

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthedUser:
    user_id: str
    jwt: str


@lru_cache(maxsize=1)
def _get_jwks_client() -> PyJWKClient | None:
    """Build a cached JWKS client from the Supabase URL."""
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not supabase_url:
        return None
    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(jwks_url, cache_keys=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    token = credentials.credentials

    try:
        # Peek at the token header to determine the algorithm
        header = pyjwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="malformed token header",
        )

    try:
        if alg == "ES256":
            # Asymmetric: fetch the signing key from Supabase JWKS
            jwks_client = _get_jwks_client()
            if jwks_client is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="SUPABASE_URL not configured (needed for JWKS)",
                )
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
            )
        else:
            # Symmetric (HS256): use the JWT secret directly
            secret = os.environ.get("SUPABASE_JWT_SECRET")
            if not secret:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="server JWT secret not configured",
                )
            payload = pyjwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
            )

    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token expired",
        )
    except pyjwt.InvalidTokenError as exc:
        logger.error("JWT decode failed (%s): %s", alg, exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {exc}",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token missing sub claim",
        )

    return AuthedUser(user_id=user_id, jwt=token)
