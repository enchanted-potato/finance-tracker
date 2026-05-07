import os
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://finance:finance@localhost:5432/finance_tracker")
os.environ.setdefault("TEST_DATABASE_URL", "postgresql://finance:finance@localhost:5432/finance_tracker")
os.environ.setdefault("DEV_USER_ID", "test-user")


@pytest.fixture
def client_with_db(db_session):
    from fastapi.testclient import TestClient
    from api.main import app
    from app.database import get_session
    from api.routers.dashboard import router as dashboard_router

    if not any(r.path.startswith("/api/dashboard") for r in app.routes):
        app.include_router(dashboard_router)

    def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_endpoints_require_auth():
    from fastapi.testclient import TestClient
    from app.config import settings
    from api.main import app

    with patch.object(settings, "dev_user_id", ""):
        with TestClient(app) as c:
            r = c.get("/api/dashboard")
    assert r.status_code == 401


def test_no_user_id_in_response(client_with_db, db_session):
    from app.models import Snapshot

    s = Snapshot(
        user_id="test-user",
        total_assets=Decimal("10000"),
        total_liabilities=Decimal("0"),
        net_worth=Decimal("10000"),
        snapshot_date=datetime(2025, 3, 15),
    )
    db_session.add(s)
    db_session.flush()

    r = client_with_db.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()

    def _no_user_id(obj):
        if isinstance(obj, dict):
            assert "user_id" not in obj, f"user_id found in {obj}"
            for v in obj.values():
                _no_user_id(v)
        elif isinstance(obj, list):
            for item in obj:
                _no_user_id(item)

    _no_user_id(body)


def test_dashboard_money_fields_are_floats(client_with_db, db_session):
    from app.models import Snapshot, AccountType, AccountEntry

    s = Snapshot(
        user_id="test-user",
        total_assets=Decimal("5000"),
        total_liabilities=Decimal("1000"),
        net_worth=Decimal("4000"),
        snapshot_date=datetime(2025, 3, 15),
    )
    db_session.add(s)
    at = AccountType(name="ISA_float_test", user_id="test-user", is_pension=False)
    db_session.add(at)
    db_session.flush()
    e = AccountEntry(
        user_id="test-user",
        account_type_id=at.id,
        entry_date=date(2025, 3, 15),
        balance=Decimal("5000"),
        exchange_rate=Decimal("1"),
    )
    db_session.add(e)
    db_session.flush()

    r = client_with_db.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()

    cards = body["cards"]
    for field in ("net_worth", "assets", "liabilities", "net_worth_delta"):
        v = cards[field]
        assert v is None or isinstance(v, float), f"cards.{field} is not float: {v!r}"

    for item in body["trend"]:
        for field in ("net_worth", "assets", "liabilities"):
            v = item[field]
            assert v is None or isinstance(v, float), f"trend.{field} is not float: {v!r}"

    for item in body["allocation"]:
        assert isinstance(item["value"], float), f"allocation.value is not float: {item['value']!r}"

    for item in body["pension"]:
        assert isinstance(item["value"], float), f"pension.value is not float: {item['value']!r}"


def test_dashboard_cards_from_latest_snapshot(client_with_db, db_session):
    from app.models import Snapshot

    for dt, nw, assets, liabilities in [
        (datetime(2025, 1, 15), Decimal("9000"), Decimal("9000"), Decimal("0")),
        (datetime(2025, 2, 15), Decimal("9500"), Decimal("9500"), Decimal("0")),
        (datetime(2025, 3, 15), Decimal("10000"), Decimal("10000"), Decimal("0")),
    ]:
        db_session.add(Snapshot(
            user_id="test-user",
            snapshot_date=dt,
            net_worth=nw,
            total_assets=assets,
            total_liabilities=liabilities,
        ))
    db_session.flush()

    r = client_with_db.get("/api/dashboard")
    assert r.status_code == 200
    cards = r.json()["cards"]
    assert cards["net_worth"] == 10000.0
    assert cards["net_worth_delta"] == 500.0
    assert cards["assets"] == 10000.0
    assert cards["liabilities"] == 0.0


def test_dashboard_trend_is_recharts_shape(client_with_db, db_session):
    from app.models import Snapshot

    for dt, nw in [
        (datetime(2025, 1, 15), Decimal("9000")),
        (datetime(2025, 2, 15), Decimal("9500")),
        (datetime(2025, 3, 15), Decimal("10000")),
    ]:
        db_session.add(Snapshot(
            user_id="test-user",
            snapshot_date=dt,
            net_worth=nw,
            total_assets=nw,
            total_liabilities=Decimal("0"),
        ))
    db_session.flush()

    r = client_with_db.get("/api/dashboard")
    assert r.status_code == 200
    trend = r.json()["trend"]
    assert len(trend) == 3

    dates = [item["date"] for item in trend]
    assert dates == sorted(dates), "trend not in ascending date order"

    for item in trend:
        assert set(item.keys()) == {"date", "net_worth", "assets", "liabilities"}
        assert len(item["date"]) == 10 and item["date"][4] == "-"


def test_dashboard_allocation_per_account_type(client_with_db, db_session):
    from app.models import AccountType, AccountEntry

    isa = AccountType(name="ISA_alloc", user_id="test-user", is_pension=False)
    broker = AccountType(name="Brokerage_alloc", user_id="test-user", is_pension=False)
    sipp = AccountType(name="SIPP_alloc", user_id="test-user", is_pension=True)
    db_session.add_all([isa, broker, sipp])
    db_session.flush()

    db_session.add(AccountEntry(
        user_id="test-user", account_type_id=isa.id,
        entry_date=date(2025, 3, 15), balance=Decimal("5000"), exchange_rate=Decimal("1"),
    ))
    db_session.add(AccountEntry(
        user_id="test-user", account_type_id=broker.id,
        entry_date=date(2025, 3, 15), balance=Decimal("3000"), exchange_rate=Decimal("1"),
    ))
    db_session.add(AccountEntry(
        user_id="test-user", account_type_id=sipp.id,
        entry_date=date(2025, 3, 15), balance=Decimal("45000"), exchange_rate=Decimal("1"),
    ))
    db_session.flush()

    r = client_with_db.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()

    alloc = {item["name"]: item["value"] for item in body["allocation"]}
    assert "ISA_alloc" in alloc
    assert alloc["ISA_alloc"] == 5000.0
    assert "Brokerage_alloc" in alloc
    assert alloc["Brokerage_alloc"] == 3000.0
    assert "SIPP_alloc" not in alloc

    pension = {item["name"]: item["value"] for item in body["pension"]}
    assert "SIPP_alloc" in pension
    assert pension["SIPP_alloc"] == 45000.0


def test_dashboard_handles_empty_state(client_with_db):
    r = client_with_db.get("/api/dashboard")
    assert r.status_code == 200
    body = r.json()
    cards = body["cards"]
    assert cards["net_worth"] is None
    assert cards["assets"] is None
    assert cards["liabilities"] is None
    assert cards["net_worth_delta"] is None
    assert body["trend"] == []
    assert body["allocation"] == []
    assert body["pension"] == []
