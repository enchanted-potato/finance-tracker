import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from loguru import logger
from sqlmodel import Session, select

from app.models import AccountEntry, AccountType, LiabilityEntry, LiabilityType, Snapshot
from app.services.account_service import _get_pension_type_ids


def capture_snapshot(
    *, session: Session, user_id: str, snapshot_date: date | None = None
) -> Snapshot:
    """Capture a point-in-time net worth snapshot.

    Computes totals from active accounts/liabilities and upserts a snapshot
    for the given date. Only one snapshot per user per day is kept.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param snapshot_date: Date for the snapshot (defaults to today).
    :returns: The created or updated snapshot.
    """
    if snapshot_date is None:
        snapshot_date = date.today()

    pension_type_ids = _get_pension_type_ids(session, user_id)
    all_accounts = _latest_account_entries(session, user_id, snapshot_date)
    liabilities = _latest_liability_entries(session, user_id, snapshot_date)

    # Build a lookup of liability type names for detail_json
    liability_type_ids = {lb.liability_type_id for lb in liabilities}
    liability_type_names: dict[int, str] = {}
    if liability_type_ids:
        lt_rows = session.exec(
            select(LiabilityType).where(LiabilityType.id.in_(liability_type_ids))
        ).all()
        liability_type_names = {lt.id: lt.name for lt in lt_rows}

    # Build a lookup of account type names for detail_json
    account_type_ids = {a.account_type_id for a in all_accounts}
    account_type_names: dict[int, str] = {}
    if account_type_ids:
        at_rows = session.exec(
            select(AccountType).where(AccountType.id.in_(account_type_ids))
        ).all()
        account_type_names = {at.id: at.name for at in at_rows}

    # Split pension vs non-pension so pension is excluded from total_assets / net_worth
    pension_accounts = [a for a in all_accounts if a.account_type_id in pension_type_ids]
    non_pension_accounts = [a for a in all_accounts if a.account_type_id not in pension_type_ids]

    total_assets = sum((a.balance * a.exchange_rate for a in non_pension_accounts), Decimal("0"))
    total_pension = sum((a.balance * a.exchange_rate for a in pension_accounts), Decimal("0"))
    total_liabilities = (
        sum((lb.amount for lb in liabilities), Decimal("0")) if liabilities else None
    )
    net_worth = (total_assets - total_liabilities) if total_liabilities is not None else None

    detail = {
        "accounts": [
            {
                "id": a.id,
                "type_id": a.account_type_id,
                "type_name": account_type_names.get(a.account_type_id, ""),
                "balance": str(a.balance),
                "currency": a.currency,
                "exchange_rate": str(a.exchange_rate),
                "balance_gbp": str(a.balance * a.exchange_rate),
            }
            for a in non_pension_accounts
        ],
        "pension_accounts": [
            {
                "id": a.id,
                "type_id": a.account_type_id,
                "type_name": account_type_names.get(a.account_type_id, ""),
                "balance": str(a.balance),
                "currency": a.currency,
                "exchange_rate": str(a.exchange_rate),
                "balance_gbp": str(a.balance * a.exchange_rate),
            }
            for a in pension_accounts
        ],
        "liabilities": [
            {
                "id": lb.id,
                "name": liability_type_names.get(lb.liability_type_id, ""),
                "entry_date": str(lb.entry_date),
                "amount": str(lb.amount),
                "type_id": lb.liability_type_id,
            }
            for lb in liabilities
        ],
        "total_pension": str(total_pension),
    }

    # Upsert: check if a snapshot already exists for this date
    snapshot_dt = datetime.combine(snapshot_date, datetime.min.time())
    existing = session.exec(
        select(Snapshot).where(Snapshot.user_id == user_id, Snapshot.snapshot_date == snapshot_dt)
    ).first()

    if existing:
        existing.total_assets = total_assets
        existing.total_liabilities = total_liabilities
        existing.net_worth = net_worth
        existing.detail_json = detail
        session.add(existing)
        session.commit()
        session.refresh(existing)
        logger.info(f"Updated snapshot for user {user_id} on {snapshot_date}")
        return existing

    snapshot = Snapshot(
        user_id=user_id,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth,
        snapshot_date=snapshot_dt,
        detail_json=detail,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    logger.info(f"Created snapshot for user {user_id} on {snapshot_date}")
    return snapshot


def get_snapshot_history(
    *,
    session: Session,
    user_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Snapshot]:
    """Query snapshot history for a user within an optional date range.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param start_date: Inclusive start date filter.
    :param end_date: Inclusive end date filter.
    :returns: List of snapshots ordered by date ascending.
    """
    statement = select(Snapshot).where(Snapshot.user_id == user_id)
    if start_date is not None:
        statement = statement.where(
            Snapshot.snapshot_date >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date is not None:
        statement = statement.where(
            Snapshot.snapshot_date <= datetime.combine(end_date, datetime.min.time())
        )
    statement = statement.order_by(Snapshot.snapshot_date.asc())
    return list(session.exec(statement).all())


def get_latest_snapshot(*, session: Session, user_id: str) -> Snapshot | None:
    """Get the most recent snapshot for a user.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :returns: The latest snapshot or None if no snapshots exist.
    """
    statement = (
        select(Snapshot)
        .where(Snapshot.user_id == user_id)
        .order_by(Snapshot.snapshot_date.desc())
        .limit(1)
    )
    return session.exec(statement).first()


def import_csv_snapshots(
    *,
    session: Session,
    user_id: str,
    file_content: str,
) -> tuple[int, int, list[str]]:
    """Import historical snapshots from CSV data.

    Expects a CSV with at least a date column and a value column.
    Attempts to auto-detect columns by header name. Supports formats like:
    - Date, Value (from portfolio exports)
    - Date, Total Assets, Total Liabilities, Net Worth (from this app's export)

    Skips rows where the date already has a snapshot (no overwrite).

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param file_content: Raw CSV string.
    :returns: Tuple of (imported_count, skipped_count, errors).
    """
    reader = csv.DictReader(io.StringIO(file_content))
    if reader.fieldnames is None:
        return 0, 0, ["CSV file is empty or has no header row."]

    # Normalise headers for flexible matching
    normalised = {h.strip().lower(): h for h in reader.fieldnames}

    # Detect date column
    date_col = None
    for candidate in ("date", "snapshot_date"):
        if candidate in normalised:
            date_col = normalised[candidate]
            break
    if date_col is None:
        return 0, 0, ["Could not find a 'Date' column in the CSV."]

    # Detect value columns
    value_col = None
    assets_col = None
    liabilities_col = None
    nw_col = None

    for key, original in normalised.items():
        if key in ("value", "portfolio value"):
            value_col = original
        elif key in ("total assets", "total_assets", "assets"):
            assets_col = original
        elif key in ("total liabilities", "total_liabilities", "liabilities"):
            liabilities_col = original
        elif key in ("net worth", "net_worth"):
            nw_col = original

    if value_col is None and assets_col is None:
        return 0, 0, [
            "Could not find a 'Value' or 'Total Assets' column in the CSV."
        ]

    imported = 0
    skipped = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        raw_date = row.get(date_col, "").strip()
        if not raw_date:
            continue

        # Parse date — try common formats
        parsed_date = _parse_date(raw_date)
        if parsed_date is None:
            errors.append(f"Row {row_num}: Could not parse date '{raw_date}'.")
            continue

        # Parse value(s)
        try:
            if assets_col:
                total_assets = _parse_decimal(row[assets_col])
                if liabilities_col:
                    total_liabilities = _parse_decimal(row[liabilities_col])
                    net_worth = (
                        _parse_decimal(row[nw_col])
                        if nw_col
                        else total_assets - total_liabilities
                    )
                else:
                    # Assets only — no liabilities data, store as NULL
                    total_liabilities = None
                    net_worth = None
            else:
                # Single value column — assets only, no liabilities data
                total_assets = _parse_decimal(row[value_col])
                total_liabilities = None
                net_worth = None
        except (InvalidOperation, ValueError, KeyError) as exc:
            errors.append(f"Row {row_num}: Bad numeric value — {exc}.")
            continue

        # Skip if snapshot already exists for this date
        snapshot_dt = datetime.combine(parsed_date, datetime.min.time())
        existing = session.exec(
            select(Snapshot).where(
                Snapshot.user_id == user_id, Snapshot.snapshot_date == snapshot_dt
            )
        ).first()
        if existing:
            skipped += 1
            continue

        snapshot = Snapshot(
            user_id=user_id,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=net_worth,
            snapshot_date=snapshot_dt,
            detail_json=None,
        )
        session.add(snapshot)
        imported += 1

    session.commit()
    logger.info(
        f"CSV import for user {user_id}: {imported} imported, {skipped} skipped, "
        f"{len(errors)} errors"
    )
    return imported, skipped, errors


def import_csv_liabilities(
    *,
    session: Session,
    user_id: str,
    file_content: str,
) -> tuple[int, int, list[str]]:
    """Update existing snapshots' total_liabilities (and recalculate net_worth) from CSV.

    Expects a CSV with a date column and a liabilities column. Only updates existing
    snapshots — does not create new ones. total_assets is left unchanged.

    :param session: Database session.
    :param user_id: Firebase UID of the owner.
    :param file_content: Raw CSV string.
    :returns: Tuple of (updated_count, skipped_count, errors).
    """
    reader = csv.DictReader(io.StringIO(file_content))
    if reader.fieldnames is None:
        return 0, 0, ["CSV file is empty or has no header row."]

    # Normalise headers for flexible matching
    normalised = {h.strip().lower(): h for h in reader.fieldnames}

    # Detect date column
    date_col = None
    for candidate in ("date", "snapshot_date"):
        if candidate in normalised:
            date_col = normalised[candidate]
            break
    if date_col is None:
        return 0, 0, ["Could not find a 'Date' column in the CSV."]

    # Detect liabilities column
    liabilities_col = None
    for candidate in ("total liabilities", "total_liabilities", "liabilities"):
        if candidate in normalised:
            liabilities_col = normalised[candidate]
            break
    if liabilities_col is None:
        return 0, 0, ["Could not find a 'Total Liabilities' column in the CSV."]

    updated = 0
    skipped = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):
        raw_date = row.get(date_col, "").strip()
        if not raw_date:
            continue

        # Parse date
        parsed_date = _parse_date(raw_date)
        if parsed_date is None:
            errors.append(f"Row {row_num}: Could not parse date '{raw_date}'.")
            continue

        # Parse liabilities value
        try:
            total_liabilities = _parse_decimal(row[liabilities_col])
        except (InvalidOperation, ValueError, KeyError) as exc:
            errors.append(f"Row {row_num}: Bad numeric value — {exc}.")
            continue

        # Find existing snapshot for this user + date
        snapshot_dt = datetime.combine(parsed_date, datetime.min.time())
        existing = session.exec(
            select(Snapshot).where(
                Snapshot.user_id == user_id, Snapshot.snapshot_date == snapshot_dt
            )
        ).first()

        if existing is None:
            skipped += 1
            continue

        # Update liabilities and recalculate net_worth; leave total_assets untouched
        # Treat NULL total_assets as Decimal("0") for net_worth calculation
        assets_for_calc = existing.total_assets if existing.total_assets is not None else Decimal("0")
        existing.total_liabilities = total_liabilities
        existing.net_worth = assets_for_calc - total_liabilities
        session.add(existing)
        updated += 1

    session.commit()
    logger.info(
        f"CSV liabilities import for user {user_id}: {updated} updated, {skipped} skipped, "
        f"{len(errors)} errors"
    )
    return updated, skipped, errors


def _parse_date(raw: str) -> date | None:
    """Try common date formats and return a date or None."""
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def update_snapshot(
    *,
    session: Session,
    snapshot_id: int,
    total_assets: Decimal,
    total_liabilities: Decimal | None,
) -> Snapshot:
    """Update a snapshot's values.

    :param session: Database session.
    :param snapshot_id: ID of the snapshot to update.
    :param total_assets: New total assets value.
    :param total_liabilities: New total liabilities value, or None if unknown.
    :returns: The updated snapshot.
    """
    snapshot = session.get(Snapshot, snapshot_id)
    if not snapshot:
        raise ValueError(f"Snapshot with id {snapshot_id} not found")

    snapshot.total_assets = total_assets
    snapshot.total_liabilities = total_liabilities
    snapshot.net_worth = (total_assets - total_liabilities) if total_liabilities is not None else None

    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    logger.info(f"Updated snapshot {snapshot_id}")
    return snapshot


def sync_snapshot_liabilities(*, session: Session, user_id: str, snapshot_date: date) -> None:
    """Update an existing snapshot's total_liabilities and net_worth from liability_entries.

    Only touches total_liabilities and net_worth — never overwrites total_assets.
    If no snapshot exists for this date, does nothing.
    """
    liabilities = _latest_liability_entries(session, user_id, snapshot_date)
    total_liabilities = sum((lb.amount for lb in liabilities), Decimal("0")) if liabilities else None

    snapshot_dt = datetime.combine(snapshot_date, datetime.min.time())
    existing = session.exec(
        select(Snapshot).where(Snapshot.user_id == user_id, Snapshot.snapshot_date == snapshot_dt)
    ).first()
    if existing is None:
        return

    existing.total_liabilities = total_liabilities
    assets = existing.total_assets if existing.total_assets is not None else Decimal("0")
    existing.net_worth = (assets - total_liabilities) if total_liabilities is not None else None
    session.add(existing)
    session.commit()
    logger.info(f"Synced liabilities for snapshot {snapshot_date} user {user_id}")


def delete_snapshot(*, session: Session, snapshot_id: int, user_id: str) -> None:
    """Delete a snapshot by ID.

    :param session: Database session.
    :param snapshot_id: ID of the snapshot to delete.
    :param user_id: Firebase UID of the owner (for ownership check).
    :raises ValueError: If the snapshot is not found or belongs to another user.
    """
    snapshot = session.exec(
        select(Snapshot).where(Snapshot.id == snapshot_id, Snapshot.user_id == user_id)
    ).first()
    if not snapshot:
        raise ValueError(f"Snapshot {snapshot_id} not found")
    session.delete(snapshot)
    session.commit()
    logger.info(f"Deleted snapshot {snapshot_id} for user {user_id}")


def _latest_liability_entries(
    session: Session, user_id: str, as_of: date
) -> list[LiabilityEntry]:
    """Return the most recent LiabilityEntry per liability type on or before as_of.

    This ensures a snapshot always carries the latest known liability balance
    even if liabilities and accounts were updated on different days.
    """
    from sqlalchemy import func
    from sqlalchemy.orm import aliased

    # Subquery: latest entry_date per (user, liability_type) on or before as_of
    sub = (
        select(
            LiabilityEntry.liability_type_id,
            func.max(LiabilityEntry.entry_date).label("max_date"),
        )
        .where(
            LiabilityEntry.user_id == user_id,
            LiabilityEntry.entry_date <= as_of,
        )
        .group_by(LiabilityEntry.liability_type_id)
        .subquery()
    )

    stmt = select(LiabilityEntry).join(
        sub,
        (LiabilityEntry.liability_type_id == sub.c.liability_type_id)
        & (LiabilityEntry.entry_date == sub.c.max_date),
    ).where(LiabilityEntry.user_id == user_id)

    return list(session.exec(stmt).all())


def _latest_account_entries(session: Session, user_id: str, as_of: date) -> list[AccountEntry]:
    """Return the most recent AccountEntry per account type on or before as_of.

    This ensures a snapshot always carries the latest known account balance
    even if accounts and liabilities were updated on different days.
    """
    from sqlalchemy import func

    sub = (
        select(
            AccountEntry.account_type_id,
            func.max(AccountEntry.entry_date).label("max_date"),
        )
        .where(
            AccountEntry.user_id == user_id,
            AccountEntry.entry_date <= as_of,
        )
        .group_by(AccountEntry.account_type_id)
        .subquery()
    )

    stmt = select(AccountEntry).join(
        sub,
        (AccountEntry.account_type_id == sub.c.account_type_id)
        & (AccountEntry.entry_date == sub.c.max_date),
    ).where(AccountEntry.user_id == user_id)

    return list(session.exec(stmt).all())


def sync_snapshot_assets(*, session: Session, user_id: str, snapshot_date: date) -> None:
    """Update an existing snapshot's total_assets and net_worth from account entries.

    Only touches total_assets and net_worth — never overwrites total_liabilities.
    If no snapshot exists for this date, creates one.
    """
    capture_snapshot(session=session, user_id=user_id, snapshot_date=snapshot_date)


def _parse_decimal(raw: str) -> Decimal:
    """Parse a string like '£ 10,753.42' or '10753.42' to Decimal."""
    cleaned = raw.strip().replace("£", "").replace("$", "").replace(",", "").strip()
    return Decimal(cleaned)
