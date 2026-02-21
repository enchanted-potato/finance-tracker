"""Firebase authentication service layer."""

import firebase_admin
from firebase_admin import auth, credentials
from loguru import logger
from sqlmodel import Session, select

from app.config import settings
from app.models import User


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
) -> User:
    """Get existing user or create new one.

    Args:
        session: SQLModel database session
        uid: Firebase user ID
        email: User email
        display_name: User display name

    Returns:
        User model instance
    """
    # Try to get existing user
    statement = select(User).where(User.id == uid)
    user = session.exec(statement).first()

    if user:
        return user

    # Create new user
    user = User(id=uid, email=email, display_name=display_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    logger.info(f"Created new user: {uid} ({email})")

    return user
