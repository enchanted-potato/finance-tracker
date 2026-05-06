"""Integration tests for /api/configure/* endpoints (account-type and liability-type CRUD)."""
import os
from unittest.mock import patch

import pytest
from sqlmodel import select

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finance_tracker_test")
os.environ.setdefault("DEV_USER_ID", "test-user")


@pytest.fixture
def client_with_db(db_session):
    """TestClient with configure router mounted and db_session override."""
    from fastapi.testclient import TestClient
    from api.main import app
    from api.routers import configure
    from app.database import get_session

    if configure.router not in [r.router for r in app.routes if hasattr(r, "router")]:
        app.include_router(configure.router)

    app.dependency_overrides[get_session] = lambda: db_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.pop(get_session, None)


def test_endpoints_require_auth(db_session):
    """GET /api/configure/account-types and DELETE and GET /api/configure/liability-types return 401."""
    from fastapi.testclient import TestClient
    from app.config import settings
    from api.main import app
    from api.routers import configure
    from app.database import get_session

    if configure.router not in [r.router for r in app.routes if hasattr(r, "router")]:
        app.include_router(configure.router)

    app.dependency_overrides[get_session] = lambda: db_session

    try:
        with patch.object(settings, "dev_user_id", ""):
            with TestClient(app, raise_server_exceptions=False) as client:
                r1 = client.get("/api/configure/account-types")
                r2 = client.delete("/api/configure/account-types/1")
                r3 = client.get("/api/configure/liability-types")
                r4 = client.delete("/api/configure/liability-types/1")
        assert r1.status_code == 401
        assert r2.status_code == 401
        assert r3.status_code == 401
        assert r4.status_code == 401
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_no_user_id_in_responses(client_with_db, db_session):
    """GET /api/configure/account-types and /liability-types responses must NOT contain user_id."""
    from app.models import AccountType, LiabilityType
    at = AccountType(name="Checking", user_id=None, is_pension=False)
    lt = LiabilityType(name="Mortgage", user_id=None)
    db_session.add(at)
    db_session.add(lt)
    db_session.flush()

    r1 = client_with_db.get("/api/configure/account-types")
    assert r1.status_code == 200
    for item in r1.json():
        assert "user_id" not in item

    r2 = client_with_db.get("/api/configure/liability-types")
    assert r2.status_code == 200
    for item in r2.json():
        assert "user_id" not in item


def test_list_account_types_includes_in_use_flag(client_with_db, db_session, make_account):
    """GET /api/configure/account-types returns {id, name, is_pension, in_use}; in_use is correct."""
    from app.models import AccountType
    # Create Checking type and give it an entry
    checking = AccountType(name="Checking", user_id=None, is_pension=False)
    db_session.add(checking)
    brokerage = AccountType(name="Brokerage", user_id=None, is_pension=False)
    db_session.add(brokerage)
    db_session.flush()

    make_account(account_type_id=checking.id)

    response = client_with_db.get("/api/configure/account-types")
    assert response.status_code == 200
    items = response.json()
    by_name = {item["name"]: item for item in items}

    assert "in_use" in by_name["Checking"]
    assert by_name["Checking"]["in_use"] is True
    assert by_name["Brokerage"]["in_use"] is False

    for item in items:
        assert {"id", "name", "is_pension", "in_use"} <= set(item.keys())


def test_create_account_type_returns_201_owned_by_user(client_with_db, db_session):
    """POST /api/configure/account-types returns 201 and the DB row is owned by test-user."""
    from app.models import AccountType
    response = client_with_db.post(
        "/api/configure/account-types",
        json={"name": "Crypto", "is_pension": False},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Crypto"
    assert body["is_pension"] is False
    assert body["in_use"] is False
    assert isinstance(body["id"], int)

    # Confirm DB row is owned by the test user
    new_type = db_session.exec(
        select(AccountType).where(AccountType.name == "Crypto")
    ).one()
    assert new_type.user_id == "test-user"


def test_delete_in_use_account_type_returns_409(client_with_db, db_session, make_account):
    """DELETE /api/configure/account-types/{id} when type is in use returns 409."""
    from app.models import AccountType
    checking = AccountType(name="CheckingInUse", user_id=None, is_pension=False)
    db_session.add(checking)
    db_session.flush()
    make_account(account_type_id=checking.id)

    response = client_with_db.delete(f"/api/configure/account-types/{checking.id}")
    assert response.status_code == 409
    assert "still reference it" in response.json().get("detail", "")


def test_delete_unused_account_type_returns_204(client_with_db, db_session):
    """DELETE /api/configure/account-types/{id} for unused type returns 204."""
    from app.models import AccountType
    crypto = AccountType(name="CryptoUnused", user_id="test-user", is_pension=False)
    db_session.add(crypto)
    db_session.flush()

    response = client_with_db.delete(f"/api/configure/account-types/{crypto.id}")
    assert response.status_code == 204

    # Confirm deletion
    remaining = db_session.exec(
        select(AccountType).where(AccountType.id == crypto.id)
    ).first()
    assert remaining is None


def test_list_liability_types_includes_in_use_flag(client_with_db, db_session, make_liability):
    """GET /api/configure/liability-types returns {id, name, in_use}; in_use is correct."""
    from app.models import LiabilityType
    mortgage = LiabilityType(name="Mortgage", user_id=None)
    student = LiabilityType(name="Student Loan", user_id=None)
    db_session.add(mortgage)
    db_session.add(student)
    db_session.flush()

    make_liability(liability_type_id=mortgage.id)

    response = client_with_db.get("/api/configure/liability-types")
    assert response.status_code == 200
    items = response.json()
    by_name = {item["name"]: item for item in items}

    assert by_name["Mortgage"]["in_use"] is True
    assert by_name["Student Loan"]["in_use"] is False

    for item in items:
        assert {"id", "name", "in_use"} <= set(item.keys())


def test_create_liability_type_returns_201_owned_by_user(client_with_db, db_session):
    """POST /api/configure/liability-types returns 201 and DB row owned by test-user."""
    from app.models import LiabilityType
    response = client_with_db.post(
        "/api/configure/liability-types",
        json={"name": "Credit Card"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Credit Card"
    assert body["in_use"] is False
    assert isinstance(body["id"], int)

    new_type = db_session.exec(
        select(LiabilityType).where(LiabilityType.name == "Credit Card")
    ).one()
    assert new_type.user_id == "test-user"


def test_delete_in_use_liability_type_returns_409(client_with_db, db_session, make_liability):
    """DELETE /api/configure/liability-types/{id} when type is in use returns 409."""
    from app.models import LiabilityType
    mortgage = LiabilityType(name="MortgageInUse", user_id=None)
    db_session.add(mortgage)
    db_session.flush()
    make_liability(liability_type_id=mortgage.id)

    response = client_with_db.delete(f"/api/configure/liability-types/{mortgage.id}")
    assert response.status_code == 409
