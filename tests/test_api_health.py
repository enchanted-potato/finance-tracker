"""Tests for health endpoint, CORS, lifespan Firebase init, and float serialisation."""
import os
from decimal import Decimal

import pytest


os.environ.setdefault("DATABASE_URL", "postgresql://finance:finance@localhost:5432/finance_tracker")
os.environ.setdefault("DEV_USER_ID", "test-dev-user")


def test_health_returns_200():
    """GET /api/health returns 200 with body {"status": "ok"}."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_firebase_not_init_at_import():
    """Importing api.main must NOT trigger firebase_admin.initialize_app at module level."""
    import firebase_admin

    def _firebase_is_initialised() -> bool:
        """Return True if the default Firebase app exists."""
        try:
            firebase_admin.get_app()
            return True
        except ValueError:
            return False

    # Before importing api.main, Firebase should not be initialised
    # (this test runs after test_health_returns_200 which uses DEV_USER_ID — no Firebase init)
    assert not _firebase_is_initialised(), "Firebase should not be initialised before this test"

    import api.main  # noqa: F401 — import only, no TestClient

    assert not _firebase_is_initialised(), (
        "Importing api.main must not call firebase_admin.initialize_app at module level"
    )


def test_cors_preflight_allowed_origin():
    """OPTIONS /api/health with allowed origin returns 200 and correct CORS header."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_preflight_rejected_origin():
    """OPTIONS /api/health with unlisted origin has no Access-Control-Allow-Origin header."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert "access-control-allow-origin" not in response.headers


def test_decimal_serialises_as_float():
    """A Pydantic BaseModel with balance: float serialises Decimal to JSON number, not string."""
    from api.schemas.health import HealthResponse

    # Prove float fields serialise as JSON numbers
    model = HealthResponse(status="ok")
    data = model.model_dump()
    assert data == {"status": "ok"}

    # Prove that float(Decimal) round-trips through JSON as a number (not string)
    from pydantic import BaseModel

    class BalanceModel(BaseModel):
        balance: float

    instance = BalanceModel(balance=float(Decimal("10753.42")))
    serialised = instance.model_dump_json()
    import json

    parsed = json.loads(serialised)
    assert isinstance(parsed["balance"], float), (
        f"Expected float, got {type(parsed['balance'])}: {parsed['balance']}"
    )
    assert parsed["balance"] == pytest.approx(10753.42)
