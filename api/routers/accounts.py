"""Accounts router — types, entries (create/delete), and date-grouped history."""
from collections import defaultdict
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.services import account_service
from app.services.snapshot_service import capture_snapshot
from app.services.type_service import account_type_usage_count
from api.dependencies import get_current_user
from api.schemas.accounts import (
    AccountEntryRequest,
    AccountEntryResponse,
    AccountTypeResponse,
    EntryItemResponse,
    HistoryDayResponse,
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/types", response_model=list[AccountTypeResponse])
def list_account_types(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[AccountTypeResponse]:
    """Return account types visible to this user with an in_use flag."""
    types = account_service.list_account_types(session=session, user_id=user_id)
    return [
        AccountTypeResponse(
            id=t.id,
            name=t.name,
            is_pension=t.is_pension,
            in_use=account_type_usage_count(session=session, type_id=t.id) > 0,
        )
        for t in types
    ]


@router.post("/entries", response_model=AccountEntryResponse, status_code=status.HTTP_201_CREATED)
def create_account_entry(
    body: AccountEntryRequest,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> AccountEntryResponse:
    """Upsert an account entry for (user, entry_date, account_type) and auto-capture a snapshot."""
    entry = account_service.upsert_account_entry(
        session=session,
        user_id=user_id,
        account_type_id=body.account_type_id,
        entry_date=body.entry_date,
        balance=Decimal(str(body.balance)),
        currency=body.currency,
        exchange_rate=Decimal(str(body.exchange_rate)),
    )
    # D-04: auto-snapshot after every balance write
    capture_snapshot(session=session, user_id=user_id, snapshot_date=entry.entry_date)
    return AccountEntryResponse(
        id=entry.id,
        account_type_id=entry.account_type_id,
        entry_date=entry.entry_date,
        balance=float(entry.balance),
        currency=entry.currency,
    )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account_entry_endpoint(
    entry_id: int,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> None:
    """Hard-delete an account entry the caller owns."""
    try:
        account_service.delete_account_entry(session=session, entry_id=entry_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/history", response_model=list[HistoryDayResponse])
def get_account_history(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[HistoryDayResponse]:
    """Return non-pension entries grouped by date, newest first, with server-computed totals."""
    entries = account_service.list_non_pension_entries(session=session, user_id=user_id)
    types = {
        t.id: t.name
        for t in account_service.list_account_types(session=session, user_id=user_id)
    }

    grouped: dict[str, list[EntryItemResponse]] = defaultdict(list)
    totals: dict[str, float] = defaultdict(float)
    for e in entries:
        day = e.entry_date.isoformat()
        gbp = float(e.balance * e.exchange_rate)
        grouped[day].append(
            EntryItemResponse(
                entry_id=e.id,
                type_id=e.account_type_id,
                type_name=types.get(e.account_type_id, ""),
                balance=gbp,
            )
        )
        totals[day] += gbp

    return [
        HistoryDayResponse(date=day, total=totals[day], entries=grouped[day])
        for day in sorted(grouped.keys(), reverse=True)
    ]
