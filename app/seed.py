from loguru import logger
from sqlmodel import Session, select

from app.models import AccountType, LiabilityType

DEFAULT_ACCOUNT_TYPES = [
    "Cash Savings",
    "Investment Account",
    "Crypto",
    "Pension",
    "Other",
]

DEFAULT_LIABILITY_TYPES = [
    "Student Loan",
    "Mortgage",
    "Credit Card",
    "Personal Loan",
    "Other",
]


def seed_default_types(*, session: Session) -> None:
    """Seed system-default account and liability types.

    Only inserts types that don't already exist (user_id=NULL).
    Safe to call multiple times.

    :param session: Database session.
    """
    _seed_account_types(session=session)
    _seed_liability_types(session=session)
    session.commit()
    logger.info("Default account and liability types seeded")


def _seed_account_types(*, session: Session) -> None:
    """Insert default account types if they don't exist."""
    existing = {
        row.name
        for row in session.exec(select(AccountType).where(AccountType.user_id.is_(None))).all()
    }
    for name in DEFAULT_ACCOUNT_TYPES:
        if name not in existing:
            session.add(AccountType(name=name, user_id=None))
            logger.debug(f"Seeding account type: {name}")


def _seed_liability_types(*, session: Session) -> None:
    """Insert default liability types if they don't exist."""
    existing = {
        row.name
        for row in session.exec(select(LiabilityType).where(LiabilityType.user_id.is_(None))).all()
    }
    for name in DEFAULT_LIABILITY_TYPES:
        if name not in existing:
            session.add(LiabilityType(name=name, user_id=None))
            logger.debug(f"Seeding liability type: {name}")
