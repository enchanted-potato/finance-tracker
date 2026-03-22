"""Goal CRUD and status computation."""

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from app.models import AccountEntry, Goal


def list_goals(*, session: Session, user_id: str) -> list[Goal]:
    """Return all goals for a user ordered by target_date asc."""
    return list(
        session.exec(
            select(Goal)
            .where(Goal.user_id == user_id)
            .order_by(Goal.target_date.asc())
        ).all()
    )


def create_goal(
    *,
    session: Session,
    user_id: str,
    name: str,
    account_type_id: int | None,
    target_amount: Decimal,
    target_date: date,
) -> Goal:
    """Create a new goal."""
    goal = Goal(
        user_id=user_id,
        name=name,
        account_type_id=account_type_id,
        target_amount=target_amount,
        target_date=target_date,
    )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


def update_goal(
    *,
    session: Session,
    goal_id: int,
    user_id: str,
    name: str,
    account_type_id: int | None,
    target_amount: Decimal,
    target_date: date,
) -> Goal:
    """Update an existing goal."""
    goal = session.exec(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    ).first()
    if not goal:
        raise ValueError(f"Goal {goal_id} not found")
    goal.name = name
    goal.account_type_id = account_type_id
    goal.target_amount = target_amount
    goal.target_date = target_date
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


def delete_goal(*, session: Session, goal_id: int, user_id: str) -> None:
    """Delete a goal."""
    goal = session.exec(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    ).first()
    if not goal:
        raise ValueError(f"Goal {goal_id} not found")
    session.delete(goal)
    session.commit()


def get_current_value(*, session: Session, user_id: str, account_type_id: int) -> Decimal:
    """Return the latest GBP balance for an account type."""
    entry = session.exec(
        select(AccountEntry)
        .where(
            AccountEntry.user_id == user_id,
            AccountEntry.account_type_id == account_type_id,
        )
        .order_by(AccountEntry.entry_date.desc())
        .limit(1)
    ).first()
    if entry is None:
        return Decimal("0")
    return entry.balance * entry.exchange_rate


def compute_status(
    *,
    goal: Goal,
    current_value: Decimal,
    today: date,
) -> str:
    """Compute goal status: 'Ahead', 'On Track', or 'Behind'.

    Expected % = elapsed time / total duration × 100.
    If actual % > expected % + 5pp → Ahead.
    If actual % < expected % - 5pp → Behind.
    Otherwise → On Track.
    """
    if goal.target_amount <= 0:
        return "On Track"

    actual_pct = float(current_value / goal.target_amount * 100)

    start = goal.created_at.date() if goal.created_at else today
    total_days = (goal.target_date - start).days
    if total_days <= 0:
        expected_pct = 100.0
    else:
        elapsed = (today - start).days
        expected_pct = min(elapsed / total_days * 100, 100.0)

    diff = actual_pct - expected_pct
    if diff > 5:
        return "Ahead"
    if diff < -5:
        return "Behind"
    return "On Track"
