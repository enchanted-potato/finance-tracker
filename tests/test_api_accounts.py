"""Integration tests for the accounts router (API-05).

RED state: these tests fail until api/routers/accounts.py is created.

NOTE: test_create_entry_triggers_capture_snapshot patches
      `api.routers.accounts.capture_snapshot` — the import-where-used path.
      This requires the router to use:
          from app.services.snapshot_service import capture_snapshot
      so that `mocker.patch("api.routers.accounts.capture_snapshot")` works.
"""
import os
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finance_tracker_test")
os.environ.setdefault("DEV_USER_ID", "test-user")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    from api.routers.accounts import router as accounts_router

    # Idempotent include: only add if not already present (Plan 05 may add permanently)
    if not any(r.path.startswith("/api/accounts") for r in app.routes):
        app.include_router(accounts_router)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_with_db(db_session):
    from fastapi.testclient import TestClient
    from api.main import app
    from app.database import get_session
    from api.routers.accounts import router as accounts_router

    if not any(r.path.startswith("/api/accounts") for r in app.routes):
        app.include_router(accounts_router)

    def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_endpoints_require_auth():
    """Without DEV_USER_ID and without a Bearer token, accounts endpoints return 401."""
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    from app.config import settings
    from api.main import app
    from api.routers.accounts import router as accounts_router

    if not any(r.path.startswith("/api/accounts") for r in app.routes):
        app.include_router(accounts_router)

    with patch.object(settings, "dev_user_id", ""):
        with TestClient(app, raise_server_exceptions=False) as client:
            response_types = client.get("/api/accounts/types")
            response_entries = client.post(
                "/api/accounts/entries",
                json={"account_type_id": 1, "entry_date": "2025-01-15", "balance": 100.0},
            )

    assert response_types.status_code == 401
    assert response_entries.status_code == 401


def test_list_account_types_returns_in_use_flag(client_with_db, db_session):
    """GET /api/accounts/types returns list with in_use flag per type; no user_id in response."""
    from app.models import AccountType, AccountEntry

    # Create two account types: one with an entry (in_use=True), one without (in_use=False)
    checking = AccountType(name="Checking", user_id=None, is_pension=False)
    isa = AccountType(name="ISA", user_id=None, is_pension=False)
    db_session.add(checking)
    db_session.add(isa)
    db_session.flush()

    # Create an entry for ISA only
    entry = AccountEntry(
        user_id="test-user",
        account_type_id=isa.id,
        entry_date=date(2025, 1, 15),
        balance=Decimal("2000.00"),
    )
    db_session.add(entry)
    db_session.flush()

    response = client_with_db.get("/api/accounts/types")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    types_by_name = {item["name"]: item for item in data}

    # Check ISA is in_use and Checking is not
    assert "ISA" in types_by_name
    assert "Checking" in types_by_name
    assert types_by_name["ISA"]["in_use"] is True
    assert types_by_name["Checking"]["in_use"] is False

    # Each item must have exactly these keys (no user_id)
    for item in data:
        assert set(item.keys()) >= {"id", "name", "is_pension", "in_use"}
        assert "user_id" not in item


def test_no_user_id_in_responses(client_with_db, db_session):
    """GET /api/accounts/types and GET /api/accounts/history responses contain no user_id."""
    from app.models import AccountType, AccountEntry

    at = AccountType(name="Savings", user_id=None, is_pension=False)
    db_session.add(at)
    db_session.flush()

    entry = AccountEntry(
        user_id="test-user",
        account_type_id=at.id,
        entry_date=date(2025, 1, 15),
        balance=Decimal("500.00"),
    )
    db_session.add(entry)
    db_session.flush()

    import json

    types_response = client_with_db.get("/api/accounts/types")
    assert types_response.status_code == 200
    types_text = json.dumps(types_response.json())
    assert "user_id" not in types_text

    history_response = client_with_db.get("/api/accounts/history")
    assert history_response.status_code == 200
    history_text = json.dumps(history_response.json())
    assert "user_id" not in history_text


def test_create_entry_returns_201_and_persists(client_with_db, db_session):
    """POST /api/accounts/entries returns 201 and the entry is persisted in the DB."""
    from app.models import AccountType, AccountEntry
    from sqlmodel import select

    at = AccountType(name="Current", user_id=None, is_pension=False)
    db_session.add(at)
    db_session.flush()

    response = client_with_db.post(
        "/api/accounts/entries",
        json={
            "account_type_id": at.id,
            "entry_date": "2025-01-15",
            "balance": 1234.56,
            "currency": "GBP",
            "exchange_rate": 1.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["account_type_id"] == at.id
    assert data["entry_date"] == "2025-01-15"
    assert isinstance(data["balance"], float)
    assert data["balance"] == pytest.approx(1234.56)
    assert data["currency"] == "GBP"
    assert "id" in data
    assert "user_id" not in data

    # Confirm persistence in DB
    entry = db_session.exec(
        select(AccountEntry).where(AccountEntry.id == data["id"])
    ).first()
    assert entry is not None
    assert entry.balance == Decimal("1234.56")


def test_create_entry_triggers_capture_snapshot(client_with_db, db_session, mocker):
    """POST /api/accounts/entries calls capture_snapshot once with the entry's date."""
    from app.models import AccountType

    at = AccountType(name="SIPP", user_id=None, is_pension=True)
    db_session.add(at)
    db_session.flush()

    # Patch at the point of use in the router module
    mock_snapshot = mocker.patch("api.routers.accounts.capture_snapshot")

    response = client_with_db.post(
        "/api/accounts/entries",
        json={
            "account_type_id": at.id,
            "entry_date": "2025-02-01",
            "balance": 5000.0,
        },
    )
    assert response.status_code == 201

    mock_snapshot.assert_called_once()
    call_kwargs = mock_snapshot.call_args.kwargs
    assert call_kwargs["user_id"] == "test-user"
    assert call_kwargs["snapshot_date"] == date(2025, 2, 1)
    assert "session" in call_kwargs


def test_balance_decimal_precision_preserved(client_with_db, db_session):
    """POST with balance 0.1 stores Decimal('0.10') in DB — not binary float representation."""
    from app.models import AccountType, AccountEntry
    from sqlmodel import select

    at = AccountType(name="Precision", user_id=None, is_pension=False)
    db_session.add(at)
    db_session.flush()

    response = client_with_db.post(
        "/api/accounts/entries",
        json={
            "account_type_id": at.id,
            "entry_date": "2025-03-01",
            "balance": 0.1,
        },
    )
    assert response.status_code == 201
    entry_id = response.json()["id"]

    entry = db_session.exec(
        select(AccountEntry).where(AccountEntry.id == entry_id)
    ).first()
    assert entry is not None
    # Must be Decimal("0.10") — NOT binary float's expanded representation
    assert str(entry.balance) == "0.10"


def test_create_entry_uses_authenticated_user_id(client_with_db, db_session):
    """POST /api/accounts/entries persists entry with user_id from auth (DEV_USER_ID), not client-supplied."""
    from app.models import AccountType, AccountEntry
    from sqlmodel import select

    at = AccountType(name="Bond", user_id=None, is_pension=False)
    db_session.add(at)
    db_session.flush()

    # Request body has no user_id field
    response = client_with_db.post(
        "/api/accounts/entries",
        json={
            "account_type_id": at.id,
            "entry_date": "2025-04-01",
            "balance": 999.99,
        },
    )
    assert response.status_code == 201
    entry_id = response.json()["id"]

    entry = db_session.exec(
        select(AccountEntry).where(AccountEntry.id == entry_id)
    ).first()
    assert entry is not None
    assert entry.user_id == "test-user"


def test_delete_entry_returns_204(client_with_db, db_session, make_account):
    """DELETE /api/accounts/entries/{id} returns 204 and removes the entry from the DB."""
    from app.models import AccountEntry
    from sqlmodel import select

    entry = make_account(balance=Decimal("750.00"), entry_date=date(2025, 5, 1))
    entry_id = entry.id

    response = client_with_db.delete(f"/api/accounts/entries/{entry_id}")
    assert response.status_code == 204
    assert response.content == b""

    deleted = db_session.exec(
        select(AccountEntry).where(AccountEntry.id == entry_id)
    ).first()
    assert deleted is None


def test_account_history_shape_grouped_by_date_newest_first(client_with_db, db_session):
    """GET /api/accounts/history returns date-grouped array with totals, newest first."""
    from app.models import AccountType, AccountEntry

    # Two non-pension types
    checking = AccountType(name="Checking", user_id=None, is_pension=False)
    isa = AccountType(name="ISA", user_id=None, is_pension=False)
    db_session.add(checking)
    db_session.add(isa)
    db_session.flush()

    # Three entries across two dates
    e1 = AccountEntry(
        user_id="test-user",
        account_type_id=checking.id,
        entry_date=date(2025, 1, 15),
        balance=Decimal("1000.00"),
    )
    e2 = AccountEntry(
        user_id="test-user",
        account_type_id=isa.id,
        entry_date=date(2025, 1, 15),
        balance=Decimal("2000.00"),
    )
    e3 = AccountEntry(
        user_id="test-user",
        account_type_id=checking.id,
        entry_date=date(2025, 2, 1),
        balance=Decimal("1500.00"),
    )
    db_session.add(e1)
    db_session.add(e2)
    db_session.add(e3)
    db_session.flush()

    response = client_with_db.get("/api/accounts/history")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2

    # Newest first
    assert data[0]["date"] == "2025-02-01"
    assert data[1]["date"] == "2025-01-15"

    # Check totals
    assert data[0]["total"] == pytest.approx(1500.0)
    assert data[1]["total"] == pytest.approx(3000.0)

    # Check entries structure
    assert len(data[0]["entries"]) == 1
    assert len(data[1]["entries"]) == 2

    # Validate entry item keys
    entry_item = data[0]["entries"][0]
    assert set(entry_item.keys()) >= {"entry_id", "type_id", "type_name", "balance"}
    assert entry_item["type_name"] == "Checking"
    assert isinstance(entry_item["balance"], float)


def test_balance_is_float_not_string(client_with_db, db_session):
    """Every response body with a balance/total field contains a float, never a string."""
    from app.models import AccountType, AccountEntry

    at = AccountType(name="Cash", user_id=None, is_pension=False)
    db_session.add(at)
    db_session.flush()

    entry = AccountEntry(
        user_id="test-user",
        account_type_id=at.id,
        entry_date=date(2025, 6, 1),
        balance=Decimal("1250.50"),
    )
    db_session.add(entry)
    db_session.flush()

    # Check history endpoint
    history_response = client_with_db.get("/api/accounts/history")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert len(history_data) > 0

    for day in history_data:
        assert isinstance(day["total"], float), f"total is not float: {type(day['total'])}"
        for item in day["entries"]:
            assert isinstance(item["balance"], float), f"balance is not float: {type(item['balance'])}"

    # Check create entry response
    create_response = client_with_db.post(
        "/api/accounts/entries",
        json={
            "account_type_id": at.id,
            "entry_date": "2025-07-01",
            "balance": 999.00,
        },
    )
    assert create_response.status_code == 201
    create_data = create_response.json()
    assert isinstance(create_data["balance"], float), f"created balance is not float: {type(create_data['balance'])}"
