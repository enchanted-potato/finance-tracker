from loguru import logger
from sqlmodel import Session, select

from app.models import Account, AccountType, LiabilityEntry, LiabilityType


def create_account_type(*, session: Session, name: str, user_id: str | None = None) -> AccountType:
    """Create a new account type.

    :param session: Database session.
    :param name: Display name for the type.
    :param user_id: Owner UID, or None for a system default.
    :returns: The newly created account type.
    """
    account_type = AccountType(name=name, user_id=user_id)
    session.add(account_type)
    session.commit()
    session.refresh(account_type)
    logger.info(f"Created account type '{name}' (id={account_type.id})")
    return account_type


def rename_account_type(*, session: Session, type_id: int, new_name: str) -> AccountType:
    """Rename an account type.

    :param session: Database session.
    :param type_id: Primary key of the account type.
    :param new_name: The new name.
    :returns: The updated account type.
    :raises ValueError: If the type is not found.
    """
    account_type = session.get(AccountType, type_id)
    if account_type is None:
        raise ValueError(f"Account type {type_id} not found")
    account_type.name = new_name
    session.add(account_type)
    session.commit()
    session.refresh(account_type)
    logger.info(f"Renamed account type {type_id} to '{new_name}'")
    return account_type


def delete_account_type(*, session: Session, type_id: int) -> None:
    """Delete an account type if no accounts reference it.

    :param session: Database session.
    :param type_id: Primary key of the account type.
    :raises ValueError: If the type is not found or is in use.
    """
    account_type = session.get(AccountType, type_id)
    if account_type is None:
        raise ValueError(f"Account type {type_id} not found")
    in_use = session.exec(
        select(Account).where(Account.account_type_id == type_id)
    ).first()
    if in_use is not None:
        raise ValueError(f"Cannot delete account type '{account_type.name}': accounts still reference it")
    session.delete(account_type)
    session.commit()
    logger.info(f"Deleted account type {type_id} ('{account_type.name}')")


def account_type_usage_count(*, session: Session, type_id: int) -> int:
    """Count how many accounts reference this type.

    :param session: Database session.
    :param type_id: Primary key of the account type.
    :returns: Number of accounts using this type.
    """
    return len(
        session.exec(select(Account).where(Account.account_type_id == type_id)).all()
    )


def create_liability_type(
    *, session: Session, name: str, user_id: str | None = None
) -> LiabilityType:
    """Create a new liability type.

    :param session: Database session.
    :param name: Display name for the type.
    :param user_id: Owner UID, or None for a system default.
    :returns: The newly created liability type.
    """
    liability_type = LiabilityType(name=name, user_id=user_id)
    session.add(liability_type)
    session.commit()
    session.refresh(liability_type)
    logger.info(f"Created liability type '{name}' (id={liability_type.id})")
    return liability_type


def rename_liability_type(*, session: Session, type_id: int, new_name: str) -> LiabilityType:
    """Rename a liability type.

    :param session: Database session.
    :param type_id: Primary key of the liability type.
    :param new_name: The new name.
    :returns: The updated liability type.
    :raises ValueError: If the type is not found.
    """
    liability_type = session.get(LiabilityType, type_id)
    if liability_type is None:
        raise ValueError(f"Liability type {type_id} not found")
    liability_type.name = new_name
    session.add(liability_type)
    session.commit()
    session.refresh(liability_type)
    logger.info(f"Renamed liability type {type_id} to '{new_name}'")
    return liability_type


def delete_liability_type(*, session: Session, type_id: int) -> None:
    """Delete a liability type if no liabilities reference it.

    :param session: Database session.
    :param type_id: Primary key of the liability type.
    :raises ValueError: If the type is not found or is in use.
    """
    liability_type = session.get(LiabilityType, type_id)
    if liability_type is None:
        raise ValueError(f"Liability type {type_id} not found")
    in_use = session.exec(
        select(LiabilityEntry).where(LiabilityEntry.liability_type_id == type_id)
    ).first()
    if in_use is not None:
        raise ValueError(
            f"Cannot delete liability type '{liability_type.name}': liabilities still reference it"
        )
    session.delete(liability_type)
    session.commit()
    logger.info(f"Deleted liability type {type_id} ('{liability_type.name}')")


def liability_type_usage_count(*, session: Session, type_id: int) -> int:
    """Count how many liabilities reference this type.

    :param session: Database session.
    :param type_id: Primary key of the liability type.
    :returns: Number of liabilities using this type.
    """
    return len(
        session.exec(
            select(LiabilityEntry).where(LiabilityEntry.liability_type_id == type_id)
        ).all()
    )
