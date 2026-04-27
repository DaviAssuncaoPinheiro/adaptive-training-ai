"""FastAPI dependency that validates Supabase access tokens.

Uses the Supabase client to validate the token natively against the Auth API.
This ensures complete compatibility with ES256 and other modern asymmetric 
JWT algorithms without needing to locally cache JWKS public keys.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthedUser:
    user_id: str
    jwt: str


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
        from supabase import create_client
        url = os.environ["SUPABASE_URL"]
        anon = os.environ["SUPABASE_ANON_KEY"]
        sb = create_client(url, anon)
        
        user_resp = sb.auth.get_user(token)
        if not user_resp or not user_resp.user:
            raise ValueError("No user returned")
            
        user_id = user_resp.user.id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {str(e)}",
        )

    return AuthedUser(user_id=user_id, jwt=token)
