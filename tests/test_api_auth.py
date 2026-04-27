"""Tests for auth dependency: 401/403 scenarios and dev bypass."""
import os

import pytest


os.environ.setdefault("DATABASE_URL", "postgresql://finance:finance@localhost:5432/finance_tracker")
# Default: no dev bypass so auth tests exercise real dependency
os.environ.setdefault("DEV_USER_ID", "")


def _make_client_no_dev_bypass():
    """Create a TestClient with dev_user_id unset so auth runs normally."""
    from fastapi.testclient import TestClient
    from unittest.mock import patch

    from app.config import settings
    from api.main import app

    with patch.object(settings, "dev_user_id", ""):
        client = TestClient(app, raise_server_exceptions=False)
    return client


def test_missing_token_returns_401():
    """GET /api/test-protected with no Authorization header returns 401."""
    from fastapi import Depends
    from fastapi.testclient import TestClient
    from unittest.mock import patch

    from app.config import settings
    from api.dependencies import get_current_user
    from api.main import app

    @app.get("/api/test-protected")
    def _protected(uid: str = Depends(get_current_user)):
        return {"uid": uid}

    with patch.object(settings, "dev_user_id", ""):
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/test-protected")
    assert response.status_code == 401


def test_invalid_token_returns_401(mocker):
    """GET /api/test-protected with invalid token returns 401."""
    from fastapi import Depends
    from fastapi.testclient import TestClient
    from unittest.mock import patch

    from app.config import settings
    from api.dependencies import get_current_user
    from api.main import app

    @app.get("/api/test-protected")
    def _protected_invalid(uid: str = Depends(get_current_user)):
        return {"uid": uid}

    mocker.patch("firebase_admin.auth.verify_id_token", side_effect=Exception("bad token"))

    with patch.object(settings, "dev_user_id", ""):
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(
                "/api/test-protected",
                headers={"Authorization": "Bearer invalidtoken"},
            )
    assert response.status_code == 401


def test_wrong_uid_returns_403(mocker):
    """GET /api/test-protected with valid token but wrong UID returns 403."""
    from fastapi import Depends
    from fastapi.testclient import TestClient
    from unittest.mock import patch

    from app.config import settings
    from api.dependencies import get_current_user
    from api.main import app

    @app.get("/api/test-protected")
    def _protected_wrong_uid(uid: str = Depends(get_current_user)):
        return {"uid": uid}

    mocker.patch(
        "firebase_admin.auth.verify_id_token",
        return_value={"uid": "wrong-uid"},
    )

    with patch.object(settings, "dev_user_id", ""), patch.object(
        settings, "allowed_firebase_uid", "expected-uid"
    ):
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(
                "/api/test-protected",
                headers={"Authorization": "Bearer somevalidtoken"},
            )
    assert response.status_code == 403


def test_dev_bypass_skips_firebase(mocker):
    """With dev_user_id set, GET /api/test-protected succeeds (200) without a token."""
    from fastapi import Depends
    from fastapi.testclient import TestClient
    from unittest.mock import patch

    from app.config import settings
    from api.dependencies import get_current_user
    from api.main import app

    @app.get("/api/test-protected")
    def _protected_bypass(uid: str = Depends(get_current_user)):
        return {"uid": uid}

    verify_mock = mocker.patch("firebase_admin.auth.verify_id_token")

    with patch.object(settings, "dev_user_id", "dev-user"):
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/test-protected")
    assert response.status_code == 200
    assert response.json() == {"uid": "dev-user"}
    verify_mock.assert_not_called()
