import os

os.environ.setdefault("DATABASE_URL", "postgresql://finance:finance@localhost:5432/finance_tracker")
os.environ.setdefault("DEV_USER_ID", "test-user")

import pytest


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    # raise_server_exceptions=False: DB errors return 500 instead of propagating —
    # this test only verifies route registration (not 404), not endpoint correctness.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


PROBES = [
    ("GET", "/api/accounts/types"),
    ("POST", "/api/accounts/entries"),
    ("DELETE", "/api/accounts/entries/0"),
    ("GET", "/api/accounts/history"),
    ("GET", "/api/liabilities/types"),
    ("POST", "/api/liabilities/entries"),
    ("DELETE", "/api/liabilities/entries/0"),
    ("GET", "/api/liabilities/history"),
    ("GET", "/api/pension/types"),
    ("POST", "/api/pension/entries"),
    ("DELETE", "/api/pension/entries/0"),
    ("GET", "/api/pension/history"),
    ("GET", "/api/snapshots"),
    ("GET", "/api/snapshots/export.csv"),
    ("POST", "/api/snapshots/import"),
    ("DELETE", "/api/snapshots/0"),
    ("GET", "/api/configure/account-types"),
    ("POST", "/api/configure/account-types"),
    ("DELETE", "/api/configure/account-types/0"),
    ("GET", "/api/configure/liability-types"),
    ("POST", "/api/configure/liability-types"),
    ("DELETE", "/api/configure/liability-types/0"),
    ("GET", "/api/dashboard"),
]


@pytest.mark.parametrize("method,path", PROBES)
def test_all_routers_mounted(client, method, path):
    """Each route prefix must be registered in main.py — probe must NOT return a route-not-found 404.

    FastAPI returns {"detail": "Not Found"} for unregistered routes; resource-not-found 404s
    from registered routes have a custom detail message, so a plain "Not Found" means the
    router is missing from api/main.py.
    """
    response = client.request(method, path)
    if response.status_code == 404:
        detail = response.json().get("detail", "")
        assert detail != "Not Found", (
            f"{method} {path} returned route-not-found 404 — router not wired into api/main.py"
        )
