"""FastAPI dependencies — authentication and shared utilities."""
from typing import Annotated

import firebase_admin.auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """Return the Firebase UID for the authenticated user.

    Dev bypass: when ``settings.dev_user_id`` is non-empty, returns it immediately
    without touching Firebase.

    :param token: Bearer token extracted from the Authorization header, or None.
    :returns: The Firebase UID string.
    :raises HTTPException 401: If the token is missing or fails Firebase verification.
    :raises HTTPException 403: If the UID does not match ``settings.allowed_firebase_uid``.
    """
    # Dev bypass — skip Firebase entirely in local dev / tests
    if settings.dev_user_id:
        return settings.dev_user_id

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        decoded = firebase_admin.auth.verify_id_token(token.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid: str = decoded["uid"]
    if settings.allowed_firebase_uid and uid != settings.allowed_firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return uid
