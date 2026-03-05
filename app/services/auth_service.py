"""Firebase authentication service layer."""

import firebase_admin
from firebase_admin import auth, credentials
from loguru import logger
from sqlmodel import Session

from app.config import settings


def init_firebase_admin() -> None:
    """Initialize Firebase Admin SDK with hot-reload protection.

    Skips init if already initialized or if credentials path is not set.
    """
    if firebase_admin._apps:
        logger.debug("Firebase Admin SDK already initialized, skipping")
        return

    if not settings.firebase_credentials_path:
        logger.warning(
            "FIREBASE_CREDENTIALS_PATH not set, skipping Firebase Admin init. "
            "Auth features will not work."
        )
        return

    try:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise


def verify_firebase_token(id_token: str) -> dict | None:
    """Verify Firebase ID token and return decoded claims.

    Args:
        id_token: Firebase ID token from client

    Returns:
        Decoded token dict with uid, email, name fields, or None if invalid
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        logger.warning("Firebase token expired")
        return None
    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase token")
        return None
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        return None


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
