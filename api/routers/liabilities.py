"""Liabilities router — types, entries (create/delete), and date-grouped history."""
from collections import defaultdict
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.services import liability_service
from app.services.snapshot_service import capture_snapshot
from app.services.type_service import liability_type_usage_count
from api.dependencies import get_current_user
from api.schemas.liabilities import (
    LiabilityEntryRequest,
    LiabilityEntryResponse,
    LiabilityHistoryDayResponse,
    LiabilityHistoryItemResponse,
    LiabilityTypeResponse,
)

router = APIRouter(prefix="/api/liabilities", tags=["liabilities"])


@router.get("/types", response_model=list[LiabilityTypeResponse])
def list_liability_types(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[LiabilityTypeResponse]:
    """Return liability types visible to this user with an in_use flag."""
    types = liability_service.list_liability_types(session=session, user_id=user_id)
    return [
        LiabilityTypeResponse(
            id=t.id,
            name=t.name,
            in_use=liability_type_usage_count(session=session, type_id=t.id) > 0,
        )
        for t in types
    ]


@router.post("/entries", response_model=LiabilityEntryResponse, status_code=status.HTTP_201_CREATED)
def create_liability_entry(
    body: LiabilityEntryRequest,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> LiabilityEntryResponse:
    """Upsert a liability entry for (user, entry_date, liability_type) and auto-capture a snapshot."""
    entry = liability_service.upsert_liability_entry(
        session=session,
        user_id=user_id,
        liability_type_id=body.liability_type_id,
        entry_date=body.entry_date,
        amount=Decimal(str(body.amount)),
        currency=body.currency,
    )
    capture_snapshot(session=session, user_id=user_id, snapshot_date=entry.entry_date)
    return LiabilityEntryResponse(
        id=entry.id,
        liability_type_id=entry.liability_type_id,
        entry_date=entry.entry_date,
        amount=float(entry.amount),
        currency=entry.currency,
    )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_liability_entry_endpoint(
    entry_id: int,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> None:
    """Hard-delete a liability entry the caller owns."""
    try:
        liability_service.delete_liability_entry(session=session, entry_id=entry_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/history", response_model=list[LiabilityHistoryDayResponse])
def get_liability_history(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[LiabilityHistoryDayResponse]:
    """Return liability entries grouped by date, newest first, with server-computed totals."""
    entries = liability_service.list_liability_entries(session=session, user_id=user_id)
    types = {
        t.id: t.name
        for t in liability_service.list_liability_types(session=session, user_id=user_id)
    }

    grouped: dict[str, list[LiabilityHistoryItemResponse]] = defaultdict(list)
    totals: dict[str, float] = defaultdict(float)
    for e in entries:
        day = e.entry_date.isoformat()
        amt = float(e.amount)
        grouped[day].append(
            LiabilityHistoryItemResponse(
                entry_id=e.id,
                type_id=e.liability_type_id,
                type_name=types.get(e.liability_type_id, ""),
                balance=amt,
            )
        )
        totals[day] += amt

    return [
        LiabilityHistoryDayResponse(date=day, total=totals[day], entries=grouped[day])
        for day in sorted(grouped.keys(), reverse=True)
    ]
