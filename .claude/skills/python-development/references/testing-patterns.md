# Testing Patterns

## Table of Contents

- [Fixture Patterns](#fixture-patterns)
- [Parametrize Patterns](#parametrize-patterns)
- [Mocking Strategy](#mocking-strategy)
- [Async Testing](#async-testing)
- [Database Testing](#database-testing)

## Fixture Patterns

### Factory Fixtures

Use factory functions to create test data with overridable defaults:

```python
@pytest.fixture
def make_user():
    def _make(
        name: str = "Alice",
        email: str = "alice@example.com",
        is_active: bool = True,
    ) -> User:
        return User(name=name, email=email, is_active=is_active)
    return _make
```

### Scoped Fixtures

Use appropriate scopes to balance isolation and speed:

```python
@pytest.fixture(scope="session")
def db_engine():
    """One engine for the entire test session."""
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Fresh session per test, rolled back after."""
    with Session(db_engine) as session:
        session.begin_nested()
        yield session
        session.rollback()
```

### Fixture Composition

Build complex fixtures by composing simpler ones:

```python
@pytest.fixture
def account_with_snapshots(db_session, make_account, make_snapshot):
    account = make_account(name="Checking")
    db_session.add(account)
    db_session.flush()
    snapshots = [make_snapshot(account_id=account.id, day_offset=i) for i in range(5)]
    db_session.add_all(snapshots)
    db_session.commit()
    return account, snapshots
```

## Parametrize Patterns

### Basic Parametrize

```python
@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        ("100.50", Decimal("100.50")),
        ("-50", Decimal("-50")),
        ("0", Decimal("0")),
    ],
)
def test_parse_amount(input_value, expected):
    assert parse_amount(input_value) == expected
```

### IDs for Readability

```python
@pytest.mark.parametrize(
    ("account_type", "expected_sign"),
    [
        (AccountType.ASSET, 1),
        (AccountType.LIABILITY, -1),
    ],
    ids=["asset-positive", "liability-negative"],
)
def test_balance_sign(account_type, expected_sign):
    ...
```

### Parametrize with Fixtures

```python
@pytest.mark.parametrize("balance", [Decimal("0"), Decimal("-100"), Decimal("999999")])
def test_account_accepts_any_balance(make_account, balance):
    account = make_account(balance=balance)
    assert account.balance == balance
```

## Mocking Strategy

### When to Mock

- External HTTP APIs
- Database calls in unit tests (use real DB in integration tests)
- File system operations
- Time-dependent code (`freezegun` or `time_machine`)
- Third-party services (Firebase, Stripe, etc.)

### When NOT to Mock

- Internal functions and classes
- Data models / Pydantic validation
- Pure business logic
- Anything you can test with real objects

### Preferred Mocking Tools

```python
# Use pytest-mock's mocker fixture (wrapper around unittest.mock)
def test_sends_notification(mocker):
    mock_send = mocker.patch("app.services.notifications.send_email")
    process_order(order)
    mock_send.assert_called_once_with(to=order.email, subject=mocker.ANY)

# Use time_machine for time-dependent tests
import time_machine

@time_machine.travel("2025-01-15 12:00:00")
def test_snapshot_uses_current_date():
    snapshot = create_daily_snapshot()
    assert snapshot.date == date(2025, 1, 15)

# Use responses or respx for HTTP mocking
import responses

@responses.activate
def test_fetches_exchange_rate():
    responses.add(responses.GET, "https://api.example.com/rate", json={"rate": 1.05})
    rate = fetch_exchange_rate("EUR")
    assert rate == 1.05
```

## Async Testing

Use `pytest-asyncio` with auto mode:

```python
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

# test file
async def test_async_fetch(async_client):
    result = await async_client.get("/health")
    assert result.status_code == 200
```

## Database Testing

### Transaction Rollback Pattern

Wrap each test in a transaction that gets rolled back:

```python
@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

### Test Data Builders

For complex domain objects, use builder-style factories:

```python
@pytest.fixture
def make_portfolio(db_session, make_account):
    def _make(*, num_accounts: int = 3, base_balance: Decimal = Decimal("1000")):
        accounts = []
        for i in range(num_accounts):
            acc = make_account(name=f"Account {i}", balance=base_balance * (i + 1))
            db_session.add(acc)
            accounts.append(acc)
        db_session.flush()
        return accounts
    return _make
```
