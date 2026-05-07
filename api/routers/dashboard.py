from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.dependencies import get_current_user
from api.schemas.dashboard import (
    AllocationSlice,
    DashboardResponse,
    MetricCards,
    PensionBar,
    TrendPoint,
)
from app.database import get_session
from app.services import account_service, snapshot_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> DashboardResponse:
    snapshots = snapshot_service.get_snapshot_history(session=session, user_id=user_id)
    latest = snapshots[-1] if snapshots else None
    previous = snapshots[-2] if len(snapshots) >= 2 else None

    cards = MetricCards(
        net_worth=float(latest.net_worth) if latest and latest.net_worth is not None else None,
        assets=float(latest.total_assets) if latest and latest.total_assets is not None else None,
        liabilities=float(latest.total_liabilities) if latest and latest.total_liabilities is not None else None,
        net_worth_delta=(
            float(latest.net_worth - previous.net_worth)
            if latest and previous and latest.net_worth is not None and previous.net_worth is not None
            else None
        ),
    )

    trend = [
        TrendPoint(
            date=s.snapshot_date.date().isoformat(),
            net_worth=float(s.net_worth) if s.net_worth is not None else None,
            assets=float(s.total_assets) if s.total_assets is not None else None,
            liabilities=float(s.total_liabilities) if s.total_liabilities is not None else None,
        )
        for s in snapshots
    ]

    non_pension = account_service.list_non_pension_entries(session=session, user_id=user_id)
    non_pension_types = {
        t.id: t.name for t in account_service.list_account_types(session=session, user_id=user_id)
    }
    seen_alloc: set[int] = set()
    allocation: list[AllocationSlice] = []
    for e in non_pension:
        if e.account_type_id in seen_alloc:
            continue
        seen_alloc.add(e.account_type_id)
        allocation.append(
            AllocationSlice(
                name=non_pension_types.get(e.account_type_id, ""),
                value=float(e.balance * e.exchange_rate),
            )
        )

    pension_entries = account_service.list_pension_entries(session=session, user_id=user_id)
    pension_types = {
        t.id: t.name for t in account_service.list_pension_types(session=session, user_id=user_id)
    }
    seen_pension: set[int] = set()
    pension_bars: list[PensionBar] = []
    for e in pension_entries:
        if e.account_type_id in seen_pension:
            continue
        seen_pension.add(e.account_type_id)
        pension_bars.append(
            PensionBar(
                name=pension_types.get(e.account_type_id, ""),
                value=float(e.balance * e.exchange_rate),
            )
        )

    return DashboardResponse(
        cards=cards,
        trend=trend,
        allocation=allocation,
        pension=pension_bars,
    )
