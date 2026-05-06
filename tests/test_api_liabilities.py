"""Integration tests for the liabilities router — types, entries, history, auth."""
import os
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finance_tracker_test")
os.environ.setdefault("DEV_USER_ID", "test-user")


@pytest.fixture
def client_with_db(db_session):
    from fastapi.testclient import TestClient
    from api.main import app
    from app.database import get_session
    from api.routers.liabilities import router as liabilities_router

    if not any(r.path.startswith("/api/liabilities") for r in app.routes):
        app.include_router(liabilities_router)

    def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_endpoints_require_auth(db_session):
    """Without DEV_USER_ID, GET /api/liabilities/types and POST /api/liabilities/entries return 401."""
    from fastapi.testclient import TestClient
    from app.config import settings
    from api.main import app
    from app.database import get_session
    from api.routers.liabilities import router as liabilities_router

    if not any(r.path.startswith("/api/liabilities") for r in app.routes):
        app.include_router(liabilities_router)

    def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override

    with patch.object(settings, "dev_user_id", ""):
        with TestClient(app, raise_server_exceptions=False) as client:
            r1 = client.get("/api/liabilities/types")
            r2 = client.post(
                "/api/liabilities/entries",
                json={"liability_type_id": 1, "entry_date": "2025-01-15", "amount": 5000.0},
            )
    app.dependency_overrides.clear()
    assert r1.status_code == 401
    assert r2.status_code == 401


def test_list_liability_types_returns_in_use_flag(client_with_db, db_session):
    """GET /api/liabilities/types returns list of {id, name, in_use}; in_use reflects whether entries exist."""
    from app.models import LiabilityType, LiabilityEntry

    # Create two types: Mortgage (with entry) and Loan (without entry)
    mortgage = LiabilityType(name="Mortgage", user_id=None)
    loan = LiabilityType(name="Loan", user_id=None)
    db_session.add(mortgage)
    db_session.add(loan)
    db_session.flush()

    # Add entry for Mortgage only
    entry = LiabilityEntry(
        user_id="test-user",
        liability_type_id=mortgage.id,
        entry_date=date(2025, 1, 15),
        amount=Decimal("200000"),
    )
    db_session.add(entry)
    db_session.flush()

    response = client_with_db.get("/api/liabilities/types")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Locate our specific types by name
    mortgage_resp = next((t for t in data if t["name"] == "Mortgage"), None)
    loan_resp = next((t for t in data if t["name"] == "Loan"), None)

    assert mortgage_resp is not None
    assert loan_resp is not None
    assert mortgage_resp["in_use"] is True
    assert loan_resp["in_use"] is False

    # user_id must NOT be present in any type response
    for t in data:
        assert "user_id" not in t


def test_no_user_id_in_responses(client_with_db, db_session):
    """Assert 'user_id' does not appear in JSON responses from /types or /history."""
    from app.models import LiabilityType, LiabilityEntry

    lt = LiabilityType(name="NoUserIDType", user_id=None)
    db_session.add(lt)
    db_session.flush()
    entry = LiabilityEntry(
        user_id="test-user",
        liability_type_id=lt.id,
        entry_date=date(2025, 3, 1),
        amount=Decimal("10000"),
    )
    db_session.add(entry)
    db_session.flush()

    types_resp = client_with_db.get("/api/liabilities/types")
    assert "user_id" not in types_resp.text

    history_resp = client_with_db.get("/api/liabilities/history")
    assert "user_id" not in history_resp.text


def test_create_entry_returns_201_and_persists(client_with_db, db_session, liability_type):
    """POST /api/liabilities/entries returns 201 with correct shape; amount is JSON number; DB row exists."""
    from app.models import LiabilityEntry
    from sqlmodel import select

    payload = {
        "liability_type_id": liability_type.id,
        "entry_date": "2025-01-15",
        "amount": 5000.50,
        "currency": "GBP",
    }

    response = client_with_db.post("/api/liabilities/entries", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["liability_type_id"] == liability_type.id
    assert data["entry_date"] == "2025-01-15"
    assert isinstance(data["amount"], float)
    assert data["amount"] == pytest.approx(5000.50)
    assert data["currency"] == "GBP"
    assert "id" in data

    # DB row should exist
    db_row = db_session.exec(
        select(LiabilityEntry).where(LiabilityEntry.id == data["id"])
    ).first()
    assert db_row is not None
    assert db_row.amount == Decimal("5000.50")


def test_create_entry_triggers_capture_snapshot(client_with_db, db_session, liability_type, mocker):
    """POST /api/liabilities/entries calls capture_snapshot with correct kwargs.

    The router must do `from app.services.snapshot_service import capture_snapshot`
    for the patch path `api.routers.liabilities.capture_snapshot` to work.
    """
    mock_snapshot = mocker.patch("api.routers.liabilities.capture_snapshot")

    payload = {
        "liability_type_id": liability_type.id,
        "entry_date": "2025-02-15",
        "amount": 15000.0,
        "currency": "GBP",
    }

    response = client_with_db.post("/api/liabilities/entries", json=payload)
    assert response.status_code == 201

    mock_snapshot.assert_called_once()
    call_kwargs = mock_snapshot.call_args.kwargs
    assert call_kwargs["user_id"] == "test-user"
    assert call_kwargs["snapshot_date"] == date(2025, 2, 15)
    assert "session" in call_kwargs


def test_amount_decimal_precision_preserved(client_with_db, db_session, liability_type):
    """POST with amount 0.1 stores Decimal('0.10') — not float binary representation."""
    from app.models import LiabilityEntry
    from sqlmodel import select

    payload = {
        "liability_type_id": liability_type.id,
        "entry_date": "2025-03-01",
        "amount": 0.1,
        "currency": "GBP",
    }

    response = client_with_db.post("/api/liabilities/entries", json=payload)
    assert response.status_code == 201

    entry_id = response.json()["id"]
    db_row = db_session.exec(
        select(LiabilityEntry).where(LiabilityEntry.id == entry_id)
    ).first()
    assert db_row is not None
    # Stored value should be exactly 0.10 — not 0.1000000000000000055511...
    assert db_row.amount == Decimal("0.10")


def test_delete_entry_returns_204(client_with_db, db_session, make_liability):
    """DELETE /api/liabilities/entries/{id} returns 204; row no longer exists in DB."""
    from app.models import LiabilityEntry
    from sqlmodel import select

    entry = make_liability(user_id="test-user", entry_date=date(2025, 4, 1), amount=Decimal("50000"))

    response = client_with_db.delete(f"/api/liabilities/entries/{entry.id}")
    assert response.status_code == 204

    db_row = db_session.exec(
        select(LiabilityEntry).where(LiabilityEntry.id == entry.id)
    ).first()
    assert db_row is None


def test_delete_other_users_entry_returns_404(client_with_db, db_session, make_liability):
    """DELETE /api/liabilities/entries/{id} for another user's entry returns 404.

    Service raises ValueError when user_id doesn't match; router maps ValueError to HTTPException(404).
    """
    # Create entry for a different user
    other_entry = make_liability(user_id="other-user", entry_date=date(2025, 5, 1), amount=Decimal("30000"))

    # Request as "test-user" (the dev bypass user)
    response = client_with_db.delete(f"/api/liabilities/entries/{other_entry.id}")
    assert response.status_code == 404


def test_liability_history_shape_grouped_by_date_newest_first(client_with_db, db_session):
    """GET /api/liabilities/history returns date-grouped array, newest first, with correct keys."""
    from app.models import LiabilityType, LiabilityEntry

    # Create two types
    mortgage = LiabilityType(name="MortgageHist", user_id=None)
    loan = LiabilityType(name="LoanHist", user_id=None)
    db_session.add(mortgage)
    db_session.add(loan)
    db_session.flush()

    # Three entries across two dates
    e1 = LiabilityEntry(user_id="test-user", liability_type_id=mortgage.id, entry_date=date(2025, 1, 15), amount=Decimal("200000"))
    e2 = LiabilityEntry(user_id="test-user", liability_type_id=loan.id, entry_date=date(2025, 1, 15), amount=Decimal("5000"))
    e3 = LiabilityEntry(user_id="test-user", liability_type_id=mortgage.id, entry_date=date(2025, 2, 1), amount=Decimal("199500"))
    db_session.add_all([e1, e2, e3])
    db_session.flush()

    response = client_with_db.get("/api/liabilities/history")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    # Find our two dates (may have other entries from other tests)
    feb_day = next((d for d in data if d["date"] == "2025-02-01"), None)
    jan_day = next((d for d in data if d["date"] == "2025-01-15"), None)

    assert feb_day is not None, "2025-02-01 not in history response"
    assert jan_day is not None, "2025-01-15 not in history response"

    # Feb comes before Jan (newest first)
    feb_idx = data.index(feb_day)
    jan_idx = data.index(jan_day)
    assert feb_idx < jan_idx, "2025-02-01 should come before 2025-01-15 (newest first)"

    # Feb: one entry, total 199500
    assert feb_day["total"] == pytest.approx(199500.0)
    assert len(feb_day["entries"]) == 1
    feb_entry = feb_day["entries"][0]
    assert feb_entry["type_name"] == "MortgageHist"
    assert feb_entry["balance"] == pytest.approx(199500.0)
    assert "entry_id" in feb_entry
    assert "type_id" in feb_entry

    # Jan: two entries, total 205000
    assert jan_day["total"] == pytest.approx(205000.0)
    assert len(jan_day["entries"]) == 2
    jan_balances = {e["type_name"]: e["balance"] for e in jan_day["entries"]}
    assert jan_balances.get("MortgageHist") == pytest.approx(200000.0)
    assert jan_balances.get("LoanHist") == pytest.approx(5000.0)


def test_balance_is_float_not_string(client_with_db, db_session, liability_type, make_liability):
    """Every total/amount/balance in JSON responses is a float instance, never str."""
    import json

    make_liability(user_id="test-user", entry_date=date(2025, 6, 1), amount=Decimal("12345.67"))

    # Test history response
    history_resp = client_with_db.get("/api/liabilities/history")
    assert history_resp.status_code == 200
    history_data = history_resp.json()

    for day in history_data:
        assert isinstance(day["total"], float), f"total should be float, got {type(day['total'])}: {day['total']}"
        for entry in day["entries"]:
            assert isinstance(entry["balance"], float), f"balance should be float, got {type(entry['balance'])}: {entry['balance']}"

    # Test create entry response
    payload = {
        "liability_type_id": liability_type.id,
        "entry_date": "2025-07-01",
        "amount": 999.99,
        "currency": "GBP",
    }
    create_resp = client_with_db.post("/api/liabilities/entries", json=payload)
    assert create_resp.status_code == 201
    create_data = create_resp.json()
    assert isinstance(create_data["amount"], float), f"amount should be float, got {type(create_data['amount'])}: {create_data['amount']}"
