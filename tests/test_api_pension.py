"""Tests for pension API endpoints: types (is_pension=True filtered), entries, history."""
import os
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finance_tracker_test")
os.environ.setdefault("DEV_USER_ID", "test-user")


@pytest.fixture
def client_with_db(db_session):
    """TestClient with pension router and db_session override; DEV_USER_ID bypass active."""
    from fastapi.testclient import TestClient
    from api.main import app
    from api.routers import pension
    from app.config import settings
    from app.database import get_session

    # Idempotent include of pension router
    _included = any(r.name == "pension" for r in app.routes if hasattr(r, "name"))
    if not _included:
        app.include_router(pension.router)

    app.dependency_overrides[get_session] = lambda: db_session
    with patch.object(settings, "dev_user_id", "test-user"):
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    app.dependency_overrides.pop(get_session, None)


def test_endpoints_require_auth(db_session):
    """With dev_user_id unset, GET /api/pension/types and POST /api/pension/entries return 401."""
    from fastapi.testclient import TestClient
    from api.main import app
    from api.routers import pension
    from app.config import settings
    from app.database import get_session

    _included = any(r.name == "pension" for r in app.routes if hasattr(r, "name"))
    if not _included:
        app.include_router(pension.router)

    app.dependency_overrides[get_session] = lambda: db_session

    with patch.object(settings, "dev_user_id", ""):
        with TestClient(app, raise_server_exceptions=False) as client:
            r1 = client.get("/api/pension/types")
            r2 = client.post("/api/pension/entries", json={
                "account_type_id": 999,
                "entry_date": "2025-01-01",
                "balance": 1000.0,
            })
    app.dependency_overrides.pop(get_session, None)

    assert r1.status_code == 401
    assert r2.status_code == 401


def test_pension_types_returns_only_is_pension_true(client_with_db, db_session):
    """GET /api/pension/types returns SIPP (is_pension=True) but not ISA (is_pension=False)."""
    from app.models import AccountType

    sipp = AccountType(name="SIPP", user_id=None, is_pension=True)
    isa = AccountType(name="ISA", user_id=None, is_pension=False)
    db_session.add(sipp)
    db_session.add(isa)
    db_session.flush()

    response = client_with_db.get("/api/pension/types")
    assert response.status_code == 200
    data = response.json()
    names = [t["name"] for t in data]
    assert "SIPP" in names
    assert "ISA" not in names


def test_no_user_id_in_responses(client_with_db, db_session):
    """GET /api/pension/types and GET /api/pension/history contain no 'user_id' key."""
    from app.models import AccountType

    sipp = AccountType(name="SIPP_nuid", user_id=None, is_pension=True)
    db_session.add(sipp)
    db_session.flush()

    r_types = client_with_db.get("/api/pension/types")
    assert r_types.status_code == 200
    for item in r_types.json():
        assert "user_id" not in item

    r_history = client_with_db.get("/api/pension/history")
    assert r_history.status_code == 200
    for day in r_history.json():
        assert "user_id" not in day
        for entry in day.get("entries", []):
            assert "user_id" not in entry


def test_create_pension_entry_returns_201_and_persists(client_with_db, db_session):
    """POST /api/pension/entries returns 201 with correct shape; entry persists in DB."""
    from app.models import AccountType, AccountEntry
    from sqlmodel import select

    sipp = AccountType(name="SIPP_persist", user_id=None, is_pension=True)
    db_session.add(sipp)
    db_session.flush()

    payload = {
        "account_type_id": sipp.id,
        "entry_date": "2025-03-01",
        "balance": 45000.00,
        "currency": "GBP",
        "exchange_rate": 1.0,
    }
    response = client_with_db.post("/api/pension/entries", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["account_type_id"] == sipp.id
    assert data["entry_date"] == "2025-03-01"
    assert data["balance"] == pytest.approx(45000.0)
    assert data["currency"] == "GBP"
    assert "id" in data
    assert "user_id" not in data

    # Confirm DB persistence
    entry = db_session.exec(
        select(AccountEntry).where(
            AccountEntry.account_type_id == sipp.id,
            AccountEntry.entry_date == date(2025, 3, 1),
        )
    ).first()
    assert entry is not None
    assert float(entry.balance) == pytest.approx(45000.0)


def test_create_entry_triggers_capture_snapshot(client_with_db, db_session, mocker):
    """POST /api/pension/entries triggers capture_snapshot with correct kwargs."""
    from app.models import AccountType

    sipp = AccountType(name="SIPP_snapshot", user_id=None, is_pension=True)
    db_session.add(sipp)
    db_session.flush()

    mock_snapshot = mocker.patch("api.routers.pension.capture_snapshot")

    payload = {
        "account_type_id": sipp.id,
        "entry_date": "2025-04-01",
        "balance": 50000.0,
        "currency": "GBP",
        "exchange_rate": 1.0,
    }
    response = client_with_db.post("/api/pension/entries", json=payload)
    assert response.status_code == 201

    mock_snapshot.assert_called_once()
    call_kwargs = mock_snapshot.call_args.kwargs
    assert call_kwargs["user_id"] == "test-user"
    assert call_kwargs["snapshot_date"] == date(2025, 4, 1)


def test_post_rejects_non_pension_account_type_id(client_with_db, db_session, mocker):
    """POST /api/pension/entries with a non-pension account_type_id returns 422."""
    from app.models import AccountType

    checking = AccountType(name="Checking_reject", user_id=None, is_pension=False)
    sipp = AccountType(name="SIPP_reject", user_id=None, is_pension=True)
    db_session.add(checking)
    db_session.add(sipp)
    db_session.flush()

    mock_snapshot = mocker.patch("api.routers.pension.capture_snapshot")

    payload = {
        "account_type_id": checking.id,
        "entry_date": "2025-05-01",
        "balance": 1000.0,
        "currency": "GBP",
        "exchange_rate": 1.0,
    }
    response = client_with_db.post("/api/pension/entries", json=payload)
    assert response.status_code in (400, 422)
    assert "pension" in response.json().get("detail", "").lower()
    mock_snapshot.assert_not_called()


def test_pension_endpoints_exclude_non_pension(client_with_db, db_session):
    """GET /api/pension/history returns only SIPP entry; ISA entry is absent."""
    from app.models import AccountType, AccountEntry

    sipp = AccountType(name="SIPP_excl", user_id=None, is_pension=True)
    isa = AccountType(name="ISA_excl", user_id=None, is_pension=False)
    db_session.add(sipp)
    db_session.add(isa)
    db_session.flush()

    sipp_entry = AccountEntry(
        user_id="test-user",
        account_type_id=sipp.id,
        entry_date=date(2025, 6, 1),
        balance=Decimal("40000"),
    )
    isa_entry = AccountEntry(
        user_id="test-user",
        account_type_id=isa.id,
        entry_date=date(2025, 6, 1),
        balance=Decimal("10000"),
    )
    db_session.add(sipp_entry)
    db_session.add(isa_entry)
    db_session.flush()

    response = client_with_db.get("/api/pension/history")
    assert response.status_code == 200
    data = response.json()

    all_type_ids = [item["type_id"] for day in data for item in day["entries"]]
    assert sipp.id in all_type_ids
    assert isa.id not in all_type_ids


def test_delete_pension_entry_returns_204(client_with_db, db_session):
    """DELETE /api/pension/entries/<id> returns 204; DB confirms deletion."""
    from app.models import AccountType, AccountEntry
    from sqlmodel import select

    sipp = AccountType(name="SIPP_del", user_id=None, is_pension=True)
    db_session.add(sipp)
    db_session.flush()

    entry = AccountEntry(
        user_id="test-user",
        account_type_id=sipp.id,
        entry_date=date(2025, 7, 1),
        balance=Decimal("30000"),
    )
    db_session.add(entry)
    db_session.flush()

    response = client_with_db.delete(f"/api/pension/entries/{entry.id}")
    assert response.status_code == 204

    deleted = db_session.exec(
        select(AccountEntry).where(AccountEntry.id == entry.id)
    ).first()
    assert deleted is None


def test_pension_history_shape_grouped_by_date_newest_first(client_with_db, db_session):
    """GET /api/pension/history returns date-grouped array newest first with correct totals."""
    from app.models import AccountType, AccountEntry

    sipp = AccountType(name="SIPP_hist", user_id=None, is_pension=True)
    avc = AccountType(name="AVC_hist", user_id=None, is_pension=True)
    db_session.add(sipp)
    db_session.add(avc)
    db_session.flush()

    entries = [
        AccountEntry(user_id="test-user", account_type_id=sipp.id,
                     entry_date=date(2025, 1, 15), balance=Decimal("40000")),
        AccountEntry(user_id="test-user", account_type_id=avc.id,
                     entry_date=date(2025, 1, 15), balance=Decimal("5000")),
        AccountEntry(user_id="test-user", account_type_id=sipp.id,
                     entry_date=date(2025, 2, 1), balance=Decimal("42000")),
    ]
    for e in entries:
        db_session.add(e)
    db_session.flush()

    response = client_with_db.get("/api/pension/history")
    assert response.status_code == 200
    data = response.json()

    # Newest first
    dates = [day["date"] for day in data]
    assert dates.index("2025-02-01") < dates.index("2025-01-15")

    # Find the two expected days
    day_feb = next(d for d in data if d["date"] == "2025-02-01")
    day_jan = next(d for d in data if d["date"] == "2025-01-15")

    assert day_feb["total"] == pytest.approx(42000.0)
    assert len(day_feb["entries"]) == 1
    assert day_feb["entries"][0]["type_name"] == "SIPP_hist"
    assert day_feb["entries"][0]["balance"] == pytest.approx(42000.0)

    assert day_jan["total"] == pytest.approx(45000.0)
    assert len(day_jan["entries"]) == 2
    jan_names = {e["type_name"] for e in day_jan["entries"]}
    assert jan_names == {"SIPP_hist", "AVC_hist"}


def test_balance_is_float_not_string(client_with_db, db_session):
    """All balance/total fields in pension JSON responses are float, not str."""
    from app.models import AccountType, AccountEntry

    sipp = AccountType(name="SIPP_float", user_id=None, is_pension=True)
    db_session.add(sipp)
    db_session.flush()

    entry = AccountEntry(
        user_id="test-user",
        account_type_id=sipp.id,
        entry_date=date(2025, 8, 1),
        balance=Decimal("12345.67"),
    )
    db_session.add(entry)
    db_session.flush()

    response = client_with_db.get("/api/pension/history")
    assert response.status_code == 200
    data = response.json()

    for day in data:
        assert isinstance(day["total"], float), f"total should be float, got {type(day['total'])}"
        for item in day["entries"]:
            assert isinstance(item["balance"], float), f"balance should be float, got {type(item['balance'])}"
