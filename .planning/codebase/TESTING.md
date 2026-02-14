# Testing Patterns

**Analysis Date:** 2026-02-14

## Test Framework

**Runner:**
- pytest 9.0.2+
- Config: `pyproject.toml`
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  pythonpath = ["."]
  ```

**Assertion Library:**
- pytest's built-in assertions (no external library)
- Assertions follow pattern: `assert actual == expected`

**Run Commands:**
```bash
pytest tests/                    # Run all tests
pytest tests/test_account_service.py    # Run single test module
pytest tests/ -v                # Verbose mode
pytest tests/ --tb=short        # Short traceback format
```

**Test Database:**
- PostgreSQL test instance required
- `TEST_DATABASE_URL` env var (defaults to `postgresql://postgres:postgres@localhost:5432/finance_tracker_test`)
- Configured in `tests/conftest.py` fixture setup

## Test File Organization

**Location:**
- Co-located with source (separate `tests/` directory pattern)
- One test file per service module:
  - `tests/test_account_service.py` ↔ `app/services/account_service.py`
  - `tests/test_snapshot_service.py` ↔ `app/services/snapshot_service.py`
  - `tests/test_liability_service.py` ↔ `app/services/liability_service.py`
  - `tests/test_type_service.py` ↔ `app/services/type_service.py`

**Naming:**
- Test module prefix: `test_`
- Test class prefix: `Test` (PascalCase)
- Test method prefix: `test_` (snake_case)

**Structure:**
```
tests/
├── conftest.py          # Pytest fixtures and configuration
├── test_account_service.py
├── test_snapshot_service.py
├── test_liability_service.py
└── test_type_service.py
```

## Test Structure

**Suite Organization:**
```python
class TestCreateAccount:
    def test_create_account_basic(self, db_session, test_user, account_type):
        # Arrange
        # Act
        account = create_account(
            session=db_session,
            user_id=test_user.id,
            account_type_id=account_type.id,
            name="Chase Checking",
            balance=Decimal("5000"),
        )
        # Assert
        assert account.id is not None
        assert account.name == "Chase Checking"
        assert account.balance == Decimal("5000")
```

**Patterns:**
- Test classes group related tests by function
- Example from `tests/test_account_service.py`: `TestCreateAccount`, `TestListAccounts`, `TestGetAccount`, `TestUpdateBalance`, `TestDeactivateAccount`, `TestListAccountTypes`
- Each class tests one service function with multiple scenarios (basic, edge cases, errors)

**Setup/Teardown:**
- No explicit setUp/tearDown; handled via pytest fixtures in conftest.py
- Database transaction rollback ensures isolation: fixture yields and then rolls back transaction after test completes

## Mocking

**Framework:** pytest-mock (builtin patching via `mocker` fixture)

**Patterns:**
- Minimal mocking observed; tests use real database with fixtures
- No mock services; SQL queries tested against real (test) database
- Example: `time_machine` library used for date/time manipulation instead of mocking datetime

```python
@time_machine.travel("2025-06-15")
def test_capture_snapshot_specific_date(self, db_session, test_user):
    snapshot = capture_snapshot(
        session=db_session, user_id=test_user.id, snapshot_date=date(2025, 6, 15)
    )
    assert snapshot.snapshot_date == datetime(2025, 6, 15)
```

**What to Mock:**
- External time/date: use `time_machine.travel()` decorator
- Do NOT mock database layer (tests use actual test DB)

**What NOT to Mock:**
- SQLModel/SQLAlchemy (tests hit real database)
- Service functions (test the actual implementation)
- Database models (use fixtures to create instances)

## Fixtures and Factories

**Test Data:**

Session fixture with transaction rollback (ensures isolation):
```python
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
```

User fixture:
```python
@pytest.fixture
def test_user(db_session):
    """Create a test user and return it."""
    user = User(id="test-user", email="test@example.com", display_name="Test User")
    db_session.add(user)
    db_session.flush()
    return user
```

Factory fixture for creating accounts (callable):
```python
@pytest.fixture
def make_account(db_session, test_user, account_type):
    """Factory fixture for creating accounts."""

    def _make(
        *,
        name: str = "Savings",
        balance: Decimal = Decimal("1000"),
        user_id: str | None = None,
        account_type_id: int | None = None,
    ) -> Account:
        account = Account(
            user_id=user_id or test_user.id,
            account_type_id=account_type_id or account_type.id,
            name=name,
            balance=balance,
        )
        db_session.add(account)
        db_session.flush()
        return account

    return _make
```

Similar factories exist for:
- `make_liability()` - creates Liability instances
- `account_type` - fixture for AccountType
- `liability_type` - fixture for LiabilityType

**Location:**
- All fixtures in `tests/conftest.py`
- Shared across all test modules
- Session-scoped engine created once, function-scoped sessions created per test

## Coverage

**Requirements:** Not explicitly enforced (no coverage configuration observed)

**View Coverage:**
Not configured; no coverage reporting setup found

## Test Types

**Unit Tests:**
- Scope: Individual service functions with different input scenarios
- Approach: Isolate function logic; use fixtures for database state setup
- Example from `tests/test_account_service.py`:
  - `test_create_account_basic()` - happy path
  - `test_create_account_default_balance()` - default parameter handling
  - `test_create_account_custom_currency()` - optional parameter variation
  - `test_list_accounts_empty()` - empty state
  - `test_list_accounts_scoped_to_user()` - multi-user isolation
  - `test_update_balance_nonexistent()` - error case

**Integration Tests:**
- Scope: Service functions interacting with database
- Approach: Test functions that call multiple queries, upsert logic, date-based operations
- Example from `tests/test_snapshot_service.py`:
  - `test_capture_snapshot_with_accounts()` - aggregates account data
  - `test_capture_snapshot_upsert_same_day()` - update vs insert logic
  - `test_import_csv_snapshots()` - CSV parsing → database insertion
  - `test_capture_snapshot_excludes_inactive()` - filtering logic

**E2E Tests:**
- Not used; no Selenium or Streamlit e2e tests found
- Streamlit UI tested manually or via separate Streamlit testing tools (not in tests/ directory)

## Common Patterns

**Async Testing:**
Not applicable; Python service functions are synchronous

**Error Testing:**
```python
def test_update_balance_nonexistent(self, db_session, test_user):
    with pytest.raises(ValueError, match="not found"):
        update_balance(
            session=db_session,
            account_id=99999,
            user_id=test_user.id,
            new_balance=Decimal("100"),
        )
```

Pattern uses `pytest.raises(ExceptionType, match="regex")` to assert:
- Exception is raised
- Exception message matches pattern
- Examples from codebase:
  - `pytest.raises(ValueError, match="not found")` - for missing resources
  - `pytest.raises(ValueError, match="deactivated")` - for inactive resource updates
  - `pytest.raises(ValueError, match="accounts still reference it")` - for foreign key constraint violations

**Test Independence:**
- Database transaction rollback ensures each test starts clean
- Fixture `db_session` is function-scoped (created per test)
- No global state between tests
- Factories create instances on demand with sensible defaults

**Parameterization:**
Not observed in current tests; all variations written as separate test methods

**Date/Time Testing:**
```python
@time_machine.travel("2025-06-15")
def test_capture_snapshot_specific_date(self, db_session, test_user):
    # Test runs as if current date is 2025-06-15
```

Uses `time_machine.travel()` decorator to pin system date/time for reproducible tests

**CSV Import Testing:**
```python
def test_import_portfolio_csv(self, db_session, test_user):
    csv_content = (
        "Year,Month,Date,Value,% Return\n"
        "2021,January,15/01/21,10753.42,4.72%\n"
    )
    imported, skipped, errors = import_csv_snapshots(
        session=db_session, user_id=test_user.id, file_content=csv_content
    )
    assert imported == 3
    assert errors == []
```

Tests include:
- Multiple CSV formats (portfolio export vs app export)
- Currency symbol parsing
- Date format variations
- Error handling and reporting

---

*Testing analysis: 2026-02-14*
