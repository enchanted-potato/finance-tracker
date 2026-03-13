import os
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models import AccountEntry, AccountType, LiabilityEntry, LiabilityType

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/finance_tracker_test",
)


@pytest.fixture(scope="session")
def db_engine():
    """Create a session-scoped engine and set up all tables."""
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Provide a function-scoped session with transaction rollback."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user():
    """Return a simple user namespace with an id attribute (no DB row needed — no FK constraint)."""
    return SimpleNamespace(id="test-user")


@pytest.fixture
def account_type(db_session):
    """Create a default account type (Checking)."""
    at = AccountType(name="Checking", user_id=None)
    db_session.add(at)
    db_session.flush()
    return at


@pytest.fixture
def liability_type(db_session):
    """Create a default liability type (Mortgage)."""
    lt = LiabilityType(name="Mortgage", user_id=None)
    db_session.add(lt)
    db_session.flush()
    return lt


@pytest.fixture
def make_account(db_session, test_user, account_type):
    """Factory fixture for creating account entries."""

    def _make(
        *,
        balance: Decimal = Decimal("1000"),
        user_id: str | None = None,
        account_type_id: int | None = None,
        entry_date: date | None = None,
    ) -> AccountEntry:
        entry = AccountEntry(
            user_id=user_id or test_user.id,
            account_type_id=account_type_id or account_type.id,
            entry_date=entry_date or date.today(),
            balance=balance,
        )
        db_session.add(entry)
        db_session.flush()
        return entry

    return _make


@pytest.fixture
def make_liability(db_session, test_user, liability_type):
    """Factory fixture for creating liabilities."""

    def _make(
        *,
        entry_date=None,
        amount: Decimal = Decimal("200000"),
        user_id: str | None = None,
        liability_type_id: int | None = None,
    ) -> LiabilityEntry:
        liability = LiabilityEntry(
            user_id=user_id or test_user.id,
            liability_type_id=liability_type_id or liability_type.id,
            entry_date=entry_date or date.today(),
            amount=amount,
        )
        db_session.add(liability)
        db_session.flush()
        return liability

    return _make
