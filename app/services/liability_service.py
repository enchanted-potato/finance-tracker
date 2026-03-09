from datetime import date as date_type
from decimal import Decimal

from sqlmodel import Session, select

from app.models import LiabilityEntry, LiabilityType


def upsert_liability_entry(
    *, session: Session, user_id: str, liability_type_id: int, entry_date: date_type, amount: Decimal, currency: str = "GBP"
) -> LiabilityEntry:
    """Insert or update a single liability entry.
    Uses the unique constraint (user_id, entry_date, liability_type_id).
    """
    existing = session.exec(
        select(LiabilityEntry).where(
            LiabilityEntry.user_id == user_id,
            LiabilityEntry.entry_date == entry_date,
            LiabilityEntry.liability_type_id == liability_type_id,
        )
    ).first()
    if existing:
        existing.amount = amount
        existing.currency = currency
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    entry = LiabilityEntry(
        user_id=user_id,
        liability_type_id=liability_type_id,
        entry_date=entry_date,
        amount=amount,
        currency=currency,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def delete_liability_entry(*, session: Session, entry_id: int, user_id: str):
    """Hard-delete a liability entry. Raises ValueError if not found."""
    entry = session.exec(
        select(LiabilityEntry).where(
            LiabilityEntry.id == entry_id,
            LiabilityEntry.user_id == user_id,
        )
    ).first()
    if entry is None:
        raise ValueError(f"LiabilityEntry {entry_id} not found for user {user_id}")
    date_affected = entry.entry_date
    session.delete(entry)
    session.commit()
    return date_affected  # caller uses this to sync snapshot


def list_liability_entries(*, session: Session, user_id: str) -> list[LiabilityEntry]:
    """All entries for a user, newest date first."""
    return list(
        session.exec(
            select(LiabilityEntry)
            .where(LiabilityEntry.user_id == user_id)
            .order_by(LiabilityEntry.entry_date.desc(), LiabilityEntry.liability_type_id)
        ).all()
    )


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
