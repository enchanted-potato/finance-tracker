"""Integration tests for /api/snapshots/* endpoints (history list, CSV export, import, delete)."""
import csv
import io
import os
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlmodel import select

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finance_tracker_test")
os.environ.setdefault("DEV_USER_ID", "test-user")


@pytest.fixture
def client_with_db(db_session):
    """TestClient with snapshots router mounted and db_session override."""
    from fastapi.testclient import TestClient
    from api.main import app
    from api.routers import snapshots
    from app.database import get_session

    if snapshots.router not in [r.router for r in app.routes if hasattr(r, "router")]:
        app.include_router(snapshots.router)

    app.dependency_overrides[get_session] = lambda: db_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.pop(get_session, None)


def _make_snapshot(db_session, *, user_id="test-user", date_str="2025-01-15",
                   total_assets="10000", total_liabilities="1000", net_worth="9000"):
    from app.models import Snapshot
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    s = Snapshot(
        user_id=user_id,
        total_assets=Decimal(total_assets),
        total_liabilities=Decimal(total_liabilities),
        net_worth=Decimal(net_worth),
        snapshot_date=dt,
    )
    db_session.add(s)
    db_session.flush()
    return s


def test_endpoints_require_auth(db_session):
    """GET /api/snapshots and /api/snapshots/export.csv and POST /api/snapshots/import return 401 without auth."""
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    from app.config import settings
    from api.main import app
    from api.routers import snapshots
    from app.database import get_session

    if snapshots.router not in [r.router for r in app.routes if hasattr(r, "router")]:
        app.include_router(snapshots.router)

    app.dependency_overrides[get_session] = lambda: db_session

    try:
        with patch.object(settings, "dev_user_id", ""):
            with TestClient(app, raise_server_exceptions=False) as client:
                r1 = client.get("/api/snapshots")
                r2 = client.get("/api/snapshots/export.csv")
                r3 = client.post("/api/snapshots/import", files={"file": ("f.csv", b"", "text/csv")})
        assert r1.status_code == 401
        assert r2.status_code == 401
        assert r3.status_code == 401
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_no_user_id_in_responses(client_with_db, db_session):
    """GET /api/snapshots response items must NOT contain user_id."""
    _make_snapshot(db_session)
    response = client_with_db.get("/api/snapshots")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    for item in items:
        assert "user_id" not in item
        assert "id" in item
        assert "snapshot_date" in item


def test_get_snapshots_returns_ascending_by_date(client_with_db, db_session):
    """GET /api/snapshots returns list ordered ascending by date."""
    _make_snapshot(db_session, date_str="2025-03-01")
    _make_snapshot(db_session, date_str="2025-01-15")
    _make_snapshot(db_session, date_str="2025-02-01")
    response = client_with_db.get("/api/snapshots")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 3
    dates = [item["snapshot_date"] for item in items]
    assert dates[0].startswith("2025-01-15")
    assert dates[1].startswith("2025-02-01")
    assert dates[2].startswith("2025-03-01")


def test_export_csv_headers_and_body(client_with_db, db_session):
    """GET /api/snapshots/export.csv returns text/csv with correct headers and parseable body."""
    _make_snapshot(db_session, date_str="2025-01-15")
    _make_snapshot(db_session, date_str="2025-02-01")
    response = client_with_db.get("/api/snapshots/export.csv")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/csv")
    assert response.headers.get("content-disposition") == "attachment; filename=snapshots.csv"
    lines = response.text.splitlines()
    assert lines[0] == "date,total_assets,total_liabilities,net_worth"
    # Parse via csv.DictReader to ensure it's valid CSV
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) == 2


def test_import_csv_returns_imported_skipped_errors(client_with_db, db_session):
    """POST /api/snapshots/import returns {imported, skipped, errors} and DB has rows."""
    from app.models import Snapshot
    csv_bytes = (
        b"date,total_assets,total_liabilities,net_worth\n"
        b"2025-05-01,10000.00,1000.00,9000.00\n"
        b"2025-05-02,11000.00,1500.00,9500.00\n"
    )
    response = client_with_db.post(
        "/api/snapshots/import",
        files={"file": ("import.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"imported": 2, "skipped": 0, "errors": []}
    # Verify DB has the rows
    rows = db_session.exec(
        select(Snapshot).where(Snapshot.user_id == "test-user")
    ).all()
    assert len(rows) == 2


def test_import_invalid_utf8_returns_400(client_with_db):
    """POST /api/snapshots/import with non-UTF-8 bytes returns 400."""
    bad_bytes = b"\xff\xfe\x00\x00not-utf8"
    response = client_with_db.post(
        "/api/snapshots/import",
        files={"file": ("bad.csv", bad_bytes, "text/csv")},
    )
    assert response.status_code == 400
    detail = response.json().get("detail", "").lower()
    assert "utf-8" in detail or "decode" in detail or "utf8" in detail


def test_delete_snapshot_returns_204(client_with_db, db_session):
    """DELETE /api/snapshots/{id} returns 204 and removes the snapshot."""
    from app.models import Snapshot
    s = _make_snapshot(db_session)
    snapshot_id = s.id
    response = client_with_db.delete(f"/api/snapshots/{snapshot_id}")
    assert response.status_code == 204
    # Confirm it's gone
    remaining = db_session.exec(
        select(Snapshot).where(Snapshot.id == snapshot_id)
    ).first()
    assert remaining is None


def test_delete_other_users_snapshot_returns_404(client_with_db, db_session):
    """DELETE /api/snapshots/{id} for another user's snapshot returns 404."""
    s = _make_snapshot(db_session, user_id="other-user")
    response = client_with_db.delete(f"/api/snapshots/{s.id}")
    assert response.status_code == 404
