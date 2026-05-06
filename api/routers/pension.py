"""Pension router — pension-only filtered view over AccountEntry / AccountType."""
from collections import defaultdict
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.services import account_service
from app.services.account_service import _get_pension_type_ids
from app.services.snapshot_service import capture_snapshot
from api.dependencies import get_current_user
from api.schemas.pension import (
    PensionEntryRequest,
    PensionEntryResponse,
    PensionHistoryDayResponse,
    PensionHistoryItemResponse,
    PensionTypeResponse,
)

router = APIRouter(prefix="/api/pension", tags=["pension"])


@router.get("/types", response_model=list[PensionTypeResponse])
def list_pension_types_endpoint(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[PensionTypeResponse]:
    """Return account types where is_pension=True (visible to this user)."""
    types = account_service.list_pension_types(session=session, user_id=user_id)
    return [
        PensionTypeResponse(id=t.id, name=t.name, is_pension=t.is_pension)
        for t in types
    ]


@router.post("/entries", response_model=PensionEntryResponse, status_code=status.HTTP_201_CREATED)
def create_pension_entry(
    body: PensionEntryRequest,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> PensionEntryResponse:
    """Upsert a pension entry; rejects non-pension account_type_id with 422."""
    pension_ids = set(_get_pension_type_ids(session, user_id))
    if body.account_type_id not in pension_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="account_type_id is not a pension type",
        )
    entry = account_service.upsert_account_entry(
        session=session,
        user_id=user_id,
        account_type_id=body.account_type_id,
        entry_date=body.entry_date,
        balance=Decimal(str(body.balance)),
        currency=body.currency,
        exchange_rate=Decimal(str(body.exchange_rate)),
    )
    capture_snapshot(session=session, user_id=user_id, snapshot_date=entry.entry_date)
    return PensionEntryResponse(
        id=entry.id,
        account_type_id=entry.account_type_id,
        entry_date=entry.entry_date,
        balance=float(entry.balance),
        currency=entry.currency,
    )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pension_entry(
    entry_id: int,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> None:
    """Hard-delete a pension entry the caller owns (uses delete_account_entry)."""
    try:
        account_service.delete_account_entry(session=session, entry_id=entry_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/history", response_model=list[PensionHistoryDayResponse])
def get_pension_history(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[PensionHistoryDayResponse]:
    """Return pension entries grouped by date, newest first, with server-computed totals."""
    entries = account_service.list_pension_entries(session=session, user_id=user_id)
    types = {
        t.id: t.name
        for t in account_service.list_pension_types(session=session, user_id=user_id)
    }

    grouped: dict[str, list[PensionHistoryItemResponse]] = defaultdict(list)
    totals: dict[str, float] = defaultdict(float)
    for e in entries:
        day = e.entry_date.isoformat()
        gbp = float(e.balance * e.exchange_rate)
        grouped[day].append(
            PensionHistoryItemResponse(
                entry_id=e.id,
                type_id=e.account_type_id,
                type_name=types.get(e.account_type_id, ""),
                balance=gbp,
            )
        )
        totals[day] += gbp

    return [
        PensionHistoryDayResponse(date=day, total=totals[day], entries=grouped[day])
        for day in sorted(grouped.keys(), reverse=True)
    ]
