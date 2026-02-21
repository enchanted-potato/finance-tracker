from decimal import Decimal

from loguru import logger
from sqlmodel import Session, select

from app.models import Liability, LiabilityType


def create_liability(
    *,
    session: Session,
    user_id: str,
    liability_type_id: int,
    name: str,
    balance: Decimal = Decimal("0"),
    currency: str = "GBP",
) -> Liability:
    """Create a new liability.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param liability_type_id: FK to liability_types.
    :param name: Display name for the liability.
    :param balance: Initial outstanding balance.
    :param currency: ISO 4217 currency code.
    :returns: The newly created liability.
    """
    liability = Liability(
        user_id=user_id,
        liability_type_id=liability_type_id,
        name=name,
        balance=balance,
        currency=currency,
    )
    session.add(liability)
    session.commit()
    session.refresh(liability)
    logger.info(f"Created liability '{name}' (id={liability.id}) for user {user_id}")
    return liability


def list_liabilities(
    *,
    session: Session,
    user_id: str,
    active_only: bool = True,
) -> list[Liability]:
    """List liabilities for a user.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param active_only: If True, exclude deactivated liabilities.
    :returns: List of liabilities.
    """
    statement = select(Liability).where(Liability.user_id == user_id)
    if active_only:
        statement = statement.where(Liability.is_active.is_(True))
    statement = statement.order_by(Liability.liability_type_id, Liability.name)
    return list(session.exec(statement).all())


def get_liability(*, session: Session, liability_id: int, user_id: str) -> Liability | None:
    """Fetch a single liability by ID.

    :param session: Database session.
    :param liability_id: Primary key of the liability.
    :param user_id: Firebase UID of the owner.
    :returns: The liability or None if not found.
    """
    statement = select(Liability).where(Liability.id == liability_id, Liability.user_id == user_id)
    return session.exec(statement).first()


def update_balance(
    *,
    session: Session,
    liability_id: int,
    user_id: str,
    new_balance: Decimal,
) -> Liability:
    """Update the balance of a liability.

    :param session: Database session.
    :param liability_id: Primary key of the liability.
    :param user_id: Firebase UID of the owner.
    :param new_balance: The new outstanding balance.
    :returns: The updated liability.
    :raises ValueError: If the liability is not found or inactive.
    """
    liability = get_liability(session=session, liability_id=liability_id, user_id=user_id)
    if liability is None:
        raise ValueError(f"Liability {liability_id} not found for user {user_id}")
    if not liability.is_active:
        raise ValueError(f"Liability {liability_id} is deactivated")
    liability.balance = new_balance
    session.add(liability)
    session.commit()
    session.refresh(liability)
    logger.info(f"Updated liability {liability_id} balance to {new_balance}")
    return liability


def deactivate_liability(*, session: Session, liability_id: int, user_id: str) -> Liability:
    """Soft-delete a liability by marking it inactive.

    :param session: Database session.
    :param liability_id: Primary key of the liability.
    :param user_id: Firebase UID of the owner.
    :returns: The deactivated liability.
    :raises ValueError: If the liability is not found.
    """
    liability = get_liability(session=session, liability_id=liability_id, user_id=user_id)
    if liability is None:
        raise ValueError(f"Liability {liability_id} not found for user {user_id}")
    liability.is_active = False
    session.add(liability)
    session.commit()
    session.refresh(liability)
    logger.info(f"Deactivated liability {liability_id}")
    return liability


def list_liability_types(*, session: Session, user_id: str) -> list[LiabilityType]:
    """List liability types visible to a user (system defaults + user custom).

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: List of liability types.
    """
    statement = select(LiabilityType).where(
        (LiabilityType.user_id.is_(None)) | (LiabilityType.user_id == user_id)
    )
    return list(session.exec(statement.order_by(LiabilityType.name)).all())
