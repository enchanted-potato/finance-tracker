"""Firebase authentication service layer."""

import firebase_admin
from firebase_admin import auth, credentials
from loguru import logger
from sqlmodel import Session

from app.config import settings


def init_firebase_admin() -> None:
    """Initialize Firebase Admin SDK with hot-reload protection.

    Uses a service account key file if FIREBASE_CREDENTIALS_PATH is set (local dev),
    otherwise uses Application Default Credentials via Cloud Run's metadata server (production).
    """
    if firebase_admin._apps:
        logger.debug("Firebase Admin SDK already initialized, skipping")
        return

    try:
        if settings.firebase_credentials_path:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            firebase_admin.initialize_app(cred)
        else:
            # Production: ADC — Cloud Run metadata server provides short-lived tokens automatically
            firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise


def verify_firebase_token(id_token: str) -> dict | None:
    """Verify Firebase ID token and return decoded claims.

    Blocks any UID not matching ALLOWED_FIREBASE_UID (if set) immediately after
    decoding — before any session state or DB calls are made.

    Args:
        id_token: Firebase ID token from client

    Returns:
        Decoded token dict with uid, email, name fields, or None if invalid/unauthorized
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
    except auth.ExpiredIdTokenError:
        logger.warning("Firebase token expired")
        return None
    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase token")
        return None
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        return None

    if settings.allowed_firebase_uid and decoded_token.get("uid") != settings.allowed_firebase_uid:
        logger.warning(f"Blocked unauthorized UID: {decoded_token.get('uid')}")
        return None

    return decoded_token


def get_or_create_user(
    session: Session, uid: str, email: str, display_name: str
) -> str:
    """Validate user ID and return it.

    Args:
        session: SQLModel database session (unused, kept for compatibility)
        uid: Firebase user ID
        email: User email (unused, kept for compatibility)
        display_name: User display name (unused, kept for compatibility)

    Returns:
        Validated Firebase UID string

    Raises:
        ValueError: If uid is 'test-user' (blocked in production)
    """
    # Block test-user from production
    if uid == 'test-user':
        raise ValueError("Invalid user_id: 'test-user' is not allowed in production")

    logger.info(f"Authenticated user: {uid} ({email})")
    return uid
