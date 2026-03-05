from datetime import date, datetime
from decimal import Decimal

import time_machine
from sqlmodel import select

from app.models import Account
from app.services.account_service import update_balance
from app.services.snapshot_service import (
    capture_snapshot,
    get_latest_snapshot,
    get_snapshot_history,
    import_csv_liabilities,
    import_csv_snapshots,
)


class TestCaptureSnapshot:
    def test_capture_snapshot_no_accounts(self, db_session, test_user):
        snapshot = capture_snapshot(session=db_session, user_id=test_user.id)
        assert snapshot.total_assets == Decimal("0")
        assert snapshot.total_liabilities == Decimal("0")
        assert snapshot.net_worth == Decimal("0")
        assert snapshot.detail_json["accounts"] == []
        assert snapshot.detail_json["liabilities"] == []

    def test_capture_snapshot_stores_non_null_values_when_empty(self, db_session, test_user):
        """capture_snapshot always stores Decimal(0), never None, even with no accounts."""
        snapshot = capture_snapshot(session=db_session, user_id=test_user.id)
        assert snapshot.total_assets is not None
        assert snapshot.total_liabilities is not None
        assert snapshot.net_worth is not None
        assert snapshot.total_assets == Decimal("0")
        assert snapshot.total_liabilities == Decimal("0")
        assert snapshot.net_worth == Decimal("0")

    def test_capture_snapshot_with_accounts(self, db_session, test_user, make_account):
        make_account(name="Checking", balance=Decimal("5000"))
        make_account(name="Savings", balance=Decimal("10000"))

        snapshot = capture_snapshot(session=db_session, user_id=test_user.id)
        assert snapshot.total_assets == Decimal("15000")
        assert snapshot.net_worth == Decimal("15000")
        assert len(snapshot.detail_json["accounts"]) == 2

    def test_capture_snapshot_with_liabilities(
        self, db_session, test_user, make_account, make_liability
    ):
        make_account(name="Checking", balance=Decimal("50000"))
        make_liability(name="Mortgage", balance=Decimal("200000"))

        snapshot = capture_snapshot(session=db_session, user_id=test_user.id)
        assert snapshot.total_assets == Decimal("50000")
        assert snapshot.total_liabilities == Decimal("200000")
        assert snapshot.net_worth == Decimal("-150000")

    def test_capture_snapshot_excludes_inactive(
        self, db_session, test_user, make_account, make_liability
    ):
        make_account(name="Active", balance=Decimal("5000"))
        inactive = make_account(name="Closed", balance=Decimal("1000"))
        inactive.is_active = False
        db_session.flush()

        snapshot = capture_snapshot(session=db_session, user_id=test_user.id)
        assert snapshot.total_assets == Decimal("5000")
        assert len(snapshot.detail_json["accounts"]) == 1

    @time_machine.travel("2025-06-15")
    def test_capture_snapshot_specific_date(self, db_session, test_user):
        snapshot = capture_snapshot(
            session=db_session, user_id=test_user.id, snapshot_date=date(2025, 6, 15)
        )
        assert snapshot.snapshot_date == datetime(2025, 6, 15)

    @time_machine.travel("2025-06-15")
    def test_capture_snapshot_upsert_same_day(self, db_session, test_user, make_account):
        make_account(name="Checking", balance=Decimal("1000"))
        snap1 = capture_snapshot(
            session=db_session, user_id=test_user.id, snapshot_date=date(2025, 6, 15)
        )
        snap1_id = snap1.id

        # Update the account balance and re-capture
        accounts = db_session.exec(select(Account).where(Account.user_id == test_user.id)).all()
        update_balance(
            session=db_session,
            account_id=accounts[0].id,
            user_id=test_user.id,
            new_balance=Decimal("5000"),
        )

        snap2 = capture_snapshot(
            session=db_session, user_id=test_user.id, snapshot_date=date(2025, 6, 15)
        )
        assert snap2.id == snap1_id  # Same row was updated
        assert snap2.total_assets == Decimal("5000")


class TestGetSnapshotHistory:
    def test_history_empty(self, db_session, test_user):
        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        assert history == []

    def test_history_ordered_by_date(self, db_session, test_user, make_account):
        make_account(name="Checking", balance=Decimal("1000"))
        capture_snapshot(session=db_session, user_id=test_user.id, snapshot_date=date(2025, 3, 1))
        capture_snapshot(session=db_session, user_id=test_user.id, snapshot_date=date(2025, 1, 1))
        capture_snapshot(session=db_session, user_id=test_user.id, snapshot_date=date(2025, 2, 1))

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        assert len(history) == 3
        dates = [s.snapshot_date for s in history]
        assert dates == sorted(dates)

    def test_history_date_range_filter(self, db_session, test_user, make_account):
        make_account(name="Checking", balance=Decimal("1000"))
        for month in range(1, 7):
            capture_snapshot(
                session=db_session,
                user_id=test_user.id,
                snapshot_date=date(2025, month, 1),
            )

        history = get_snapshot_history(
            session=db_session,
            user_id=test_user.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 5, 1),
        )
        assert len(history) == 3

    def test_history_scoped_to_user(self, db_session, test_user, make_account):
        other_user_id = "other-snapshot-user"

        make_account(name="Checking", balance=Decimal("1000"))
        capture_snapshot(session=db_session, user_id=test_user.id, snapshot_date=date(2025, 1, 1))
        capture_snapshot(session=db_session, user_id=other_user_id, snapshot_date=date(2025, 1, 1))

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        assert len(history) == 1


class TestGetLatestSnapshot:
    def test_latest_when_none(self, db_session, test_user):
        latest = get_latest_snapshot(session=db_session, user_id=test_user.id)
        assert latest is None

    def test_latest_returns_most_recent(self, db_session, test_user, make_account):
        make_account(name="Checking", balance=Decimal("1000"))
        capture_snapshot(session=db_session, user_id=test_user.id, snapshot_date=date(2025, 1, 1))
        capture_snapshot(session=db_session, user_id=test_user.id, snapshot_date=date(2025, 6, 1))
        capture_snapshot(session=db_session, user_id=test_user.id, snapshot_date=date(2025, 3, 1))

        latest = get_latest_snapshot(session=db_session, user_id=test_user.id)
        assert latest is not None
        assert latest.snapshot_date == datetime(2025, 6, 1)


class TestImportCsvSnapshots:
    def test_import_portfolio_csv(self, db_session, test_user):
        csv_content = (
            "Year,Month,Date,Value,% Return\n"
            "2021,January,15/01/21,10753.42,4.72%\n"
            "2021,February,23/02/21,11873.31,6.18%\n"
            "2021,March,31/03/21,14609.71,5.70%\n"
        )
        imported, skipped, errors = import_csv_snapshots(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )
        assert imported == 3
        assert skipped == 0
        assert errors == []

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        assert len(history) == 3
        assert history[0].total_assets == Decimal("10753.42")
        assert history[0].net_worth is None
        assert history[0].total_liabilities is None
        assert history[0].snapshot_date == datetime(2021, 1, 15)

    def test_import_single_value_csv_sets_null_liabilities(self, db_session, test_user):
        """Single-value CSV (Date,Value) sets total_liabilities=None and net_worth=None."""
        csv_content = "Date,Value\n2025-01-15,15000.00\n"
        imported, skipped, errors = import_csv_snapshots(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )
        assert imported == 1
        assert errors == []

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        snap = history[0]
        assert snap.total_assets == Decimal("15000.00")
        assert snap.total_liabilities is None
        assert snap.net_worth is None

    def test_import_assets_only_csv_sets_null_liabilities(self, db_session, test_user):
        """CSV with assets column but no liabilities column sets total_liabilities=None and net_worth=None."""
        csv_content = "Date,Total Assets\n2025-02-01,20000.00\n"
        imported, skipped, errors = import_csv_snapshots(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )
        assert imported == 1
        assert errors == []

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        snap = history[0]
        assert snap.total_assets == Decimal("20000.00")
        assert snap.total_liabilities is None
        assert snap.net_worth is None

    def test_import_app_export_csv(self, db_session, test_user):
        csv_content = (
            "Date,Total Assets,Total Liabilities,Net Worth\n"
            "2025-01-01,50000.00,20000.00,30000.00\n"
            "2025-02-01,52000.00,19500.00,32500.00\n"
        )
        imported, skipped, errors = import_csv_snapshots(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )
        assert imported == 2
        assert errors == []

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        assert history[0].total_assets == Decimal("50000.00")
        assert history[0].total_liabilities == Decimal("20000.00")
        assert history[0].net_worth == Decimal("30000.00")

    def test_import_skips_existing_dates(self, db_session, test_user, make_account):
        make_account(name="Checking", balance=Decimal("1000"))
        capture_snapshot(
            session=db_session, user_id=test_user.id, snapshot_date=date(2025, 1, 1)
        )

        csv_content = (
            "Date,Value\n"
            "2025-01-01,9999.00\n"
            "2025-02-01,8888.00\n"
        )
        imported, skipped, errors = import_csv_snapshots(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )
        assert imported == 1
        assert skipped == 1

    def test_import_bad_date(self, db_session, test_user):
        csv_content = "Date,Value\nnot-a-date,1000\n"
        imported, skipped, errors = import_csv_snapshots(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )
        assert imported == 0
        assert len(errors) == 1
        assert "Could not parse date" in errors[0]

    def test_import_missing_value_column(self, db_session, test_user):
        csv_content = "Date,Something\n2025-01-01,foo\n"
        imported, skipped, errors = import_csv_snapshots(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )
        assert imported == 0
        assert "Could not find a 'Value'" in errors[0]

    def test_import_currency_symbols(self, db_session, test_user):
        csv_content = 'Date,Value\n15/01/21,"£ 10,753.42"\n'
        imported, skipped, errors = import_csv_snapshots(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )
        assert imported == 1
        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        assert history[0].total_assets == Decimal("10753.42")


class TestImportCsvLiabilities:
    def test_updates_existing_snapshot(self, db_session, test_user, make_account):
        """Liabilities and net_worth are updated on an existing snapshot."""
        make_account(name="Savings", balance=Decimal("50000"))
        capture_snapshot(
            session=db_session, user_id=test_user.id, snapshot_date=date(2025, 8, 11)
        )

        csv_content = "Date,Total Liabilities\n2025-08-11,5000.00\n"
        updated, skipped, errors = import_csv_liabilities(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )

        assert updated == 1
        assert skipped == 0
        assert errors == []

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        assert len(history) == 1
        snap = history[0]
        assert snap.total_liabilities == Decimal("5000.00")
        assert snap.net_worth == snap.total_assets - Decimal("5000.00")

    def test_skips_missing_date(self, db_session, test_user):
        """Rows with no matching snapshot are counted as skipped."""
        csv_content = "Date,Total Liabilities\n2025-07-23,4500.00\n"
        updated, skipped, errors = import_csv_liabilities(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )

        assert updated == 0
        assert skipped == 1
        assert errors == []

    def test_invalid_row_produces_error(self, db_session, test_user, make_account):
        """A row with bad numeric data produces an error entry and does not crash."""
        make_account(name="Savings", balance=Decimal("50000"))
        capture_snapshot(
            session=db_session, user_id=test_user.id, snapshot_date=date(2025, 8, 11)
        )

        csv_content = "Date,Total Liabilities\n2025-08-11,not-a-number\n"
        updated, skipped, errors = import_csv_liabilities(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )

        assert updated == 0
        assert len(errors) == 1
        assert "Row 2" in errors[0]

    def test_only_liabilities_updated(self, db_session, test_user, make_account):
        """total_assets is unchanged after a liabilities import."""
        make_account(name="Savings", balance=Decimal("75000"))
        snap_before = capture_snapshot(
            session=db_session, user_id=test_user.id, snapshot_date=date(2025, 8, 11)
        )
        original_assets = snap_before.total_assets

        csv_content = "Date,Total Liabilities\n2025-08-11,12000.00\n"
        import_csv_liabilities(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        snap_after = history[0]
        assert snap_after.total_assets == original_assets
        assert snap_after.total_liabilities == Decimal("12000.00")
        assert snap_after.net_worth == original_assets - Decimal("12000.00")

    def test_import_liabilities_when_total_assets_is_null(self, db_session, test_user):
        """import_csv_liabilities recalculates net_worth even when existing snapshot has NULL total_assets."""
        from app.models import Snapshot
        from datetime import datetime

        # Create a snapshot with total_assets=None (asset-only import scenario that was then updated)
        snapshot_dt = datetime(2025, 9, 1)
        snap = Snapshot(
            user_id=test_user.id,
            total_assets=None,
            total_liabilities=None,
            net_worth=None,
            snapshot_date=snapshot_dt,
            detail_json=None,
        )
        db_session.add(snap)
        db_session.flush()

        csv_content = "Date,Total Liabilities\n2025-09-01,3000.00\n"
        updated, skipped, errors = import_csv_liabilities(
            session=db_session, user_id=test_user.id, file_content=csv_content
        )

        assert updated == 1
        assert errors == []

        history = get_snapshot_history(session=db_session, user_id=test_user.id)
        snap_after = history[0]
        assert snap_after.total_liabilities == Decimal("3000.00")
        # When total_assets is None, treat as 0 for net_worth calculation
        assert snap_after.net_worth == Decimal("0") - Decimal("3000.00")
