from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from app.models import AccountEntry, AccountType

PENSION_TYPE_NAME = "Pension"


def _get_pension_type_id(session: Session, user_id: str) -> int | None:
    """Return the AccountType.id for 'Pension' visible to this user, or None.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: The id of the Pension account type, or None if not found.
    """
    statement = select(AccountType).where(
        (AccountType.name == PENSION_TYPE_NAME),
        (AccountType.user_id.is_(None)) | (AccountType.user_id == user_id),
    )
    at = session.exec(statement).first()
    return at.id if at else None


def upsert_account_entry(
    *,
    session: Session,
    user_id: str,
    account_type_id: int,
    entry_date: date,
    balance: Decimal = Decimal("0"),
) -> AccountEntry:
    """Insert or update an account entry by (user_id, entry_date, account_type_id).

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param account_type_id: FK to account_types.
    :param entry_date: The date this balance entry is for.
    :param balance: Balance in GBP.
    :returns: The created or updated account entry.
    """
    existing = session.exec(
        select(AccountEntry).where(
            AccountEntry.user_id == user_id,
            AccountEntry.account_type_id == account_type_id,
            AccountEntry.entry_date == entry_date,
        )
    ).first()
    if existing:
        existing.balance = balance
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    entry = AccountEntry(
        user_id=user_id,
        account_type_id=account_type_id,
        entry_date=entry_date,
        balance=balance,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def delete_account_entry(*, session: Session, entry_id: int, user_id: str) -> date:
    """Hard-delete an account entry. Returns the affected entry_date.

    :param session: Database session.
    :param entry_id: Primary key of the account entry.
    :param user_id: Firebase UID of the owner.
    :returns: The entry_date of the deleted entry.
    :raises ValueError: If the entry is not found.
    """
    entry = session.exec(
        select(AccountEntry).where(
            AccountEntry.id == entry_id, AccountEntry.user_id == user_id
        )
    ).first()
    if entry is None:
        raise ValueError(f"Account entry {entry_id} not found for user {user_id}")
    date_affected = entry.entry_date
    session.delete(entry)
    session.commit()
    return date_affected


def list_account_entries(*, session: Session, user_id: str) -> list[AccountEntry]:
    """All account entries for a user, newest date first.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: List of account entries ordered by entry_date DESC, account_type_id.
    """
    statement = (
        select(AccountEntry)
        .where(AccountEntry.user_id == user_id)
        .order_by(AccountEntry.entry_date.desc(), AccountEntry.account_type_id)
    )
    return list(session.exec(statement).all())


def list_pension_entries(*, session: Session, user_id: str) -> list[AccountEntry]:
    """Account entries where account_type_id matches the Pension type.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: List of pension entries ordered by entry_date DESC.
    """
    pension_type_id = _get_pension_type_id(session, user_id)
    if pension_type_id is None:
        return []
    statement = (
        select(AccountEntry)
        .where(
            AccountEntry.user_id == user_id,
            AccountEntry.account_type_id == pension_type_id,
        )
        .order_by(AccountEntry.entry_date.desc())
    )
    return list(session.exec(statement).all())


def list_non_pension_entries(*, session: Session, user_id: str) -> list[AccountEntry]:
    """Account entries where account_type_id does NOT match the Pension type.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: List of non-pension entries ordered by entry_date DESC, account_type_id.
    """
    pension_type_id = _get_pension_type_id(session, user_id)
    statement = select(AccountEntry).where(AccountEntry.user_id == user_id)
    if pension_type_id is not None:
        statement = statement.where(AccountEntry.account_type_id != pension_type_id)
    statement = statement.order_by(AccountEntry.entry_date.desc(), AccountEntry.account_type_id)
    return list(session.exec(statement).all())


def list_account_types(*, session: Session, user_id: str) -> list[AccountType]:
    """List account types visible to a user (system defaults + user custom).

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: List of account types.
    """
    statement = select(AccountType).where(
        (AccountType.user_id.is_(None)) | (AccountType.user_id == user_id)
    )
    return list(session.exec(statement.order_by(AccountType.name)).all())
