# Net Worth Tracker — Implementation Plan

## Overview
Track total net worth over time by recording account balances (assets) and liabilities. Visualize trends with meaningful graphs — no individual transaction tracking.

## Stack
- **Backend:** Python 3.12+ (SQLModel ORM, psycopg2)
- **Frontend:** Streamlit
- **Database:** Google Cloud SQL (PostgreSQL, free-tier `db-f1-micro`)
- **Auth:** Firebase Authentication (email/password + Google sign-in)
- **Deployment:** Google Cloud Run (containerized, free tier)
- **Package manager:** uv
- **Linting & formatting:** Ruff
- **Logging:** loguru
- **Config:** pydantic-settings (`BaseSettings` + `.env`)

## Project Structure

```
finance-tracker/
├── pyproject.toml
├── uv.lock
├── .python-version           # Pinned to 3.12
├── .gitignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── app/
│   ├── __init__.py
│   ├── config.py              # pydantic-settings BaseSettings class
│   ├── database.py            # SQLModel engine + session
│   ├── models.py              # SQLModel models: User, Account, Liability, Snapshot
│   ├── auth.py                # Firebase token verification
│   ├── seed.py                # Seed default account/liability types
│   └── services/
│       ├── __init__.py
│       ├── account_service.py # CRUD for accounts (assets)
│       ├── liability_service.py # CRUD for liabilities
│       └── snapshot_service.py  # Record & query net worth snapshots
├── frontend/
│   ├── app.py                 # Streamlit entry point + routing
│   ├── auth_component.py      # Login/signup UI
│   ├── firebase_auth.html     # Firebase JS SDK login widget
│   └── pages/
│       ├── dashboard.py       # Net worth overview + graphs
│       ├── accounts.py        # Manage asset accounts
│       ├── liabilities.py     # Manage liabilities
│       └── history.py         # Net worth history table + trend
└── tests/
    ├── __init__.py
    ├── conftest.py            # Shared fixtures: db_session, factory fixtures
    ├── test_account_service.py
    ├── test_liability_service.py
    └── test_snapshot_service.py
```

No REST API layer — Streamlit runs server-side Python, so frontend pages import service functions directly.

## Code Standards

All code must follow the project's Python development conventions:

- **Modern type hints** — `str | None` not `Optional[str]`, `list[int]` not `List[int]`
- **Keyword-only args** — use `*` separator for functions with 3+ parameters
- **f-strings everywhere** — no `.format()` or `%`
- **Sphinx-style docstrings** — for public functions and classes (no types in docstrings)
- **Naming** — `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants, boolean predicates (`is_active`, `has_permission`)
- **Error handling** — use built-in exceptions (`ValueError`, `TypeError`, etc.), let exceptions propagate, log with `loguru`
- **No `Any`** — use `object` or proper generics
- **Private helpers** — prefix with `_`

## Configuration Pattern

`app/config.py` uses `pydantic-settings`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    firebase_credentials_path: str
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

## Database Schema

### users
Mirrors Firebase auth.
| Column       | Type         | Notes                    |
|-------------|-------------|--------------------------|
| id          | VARCHAR (PK) | Firebase UID             |
| email       | VARCHAR      |                          |
| display_name| VARCHAR      |                          |
| created_at  | TIMESTAMP    | Default now()            |

### account_types
Predefined categories for asset accounts.
| Column  | Type         | Notes                                  |
|--------|-------------|----------------------------------------|
| id     | SERIAL (PK)  |                                        |
| name   | VARCHAR      | e.g. Checking, Savings, Brokerage, Retirement, Crypto, Real Estate, Other |
| user_id| VARCHAR (FK) | NULL = system default, non-NULL = custom |

`UNIQUE(name, user_id)`

### accounts
User's asset accounts with current balances.
| Column         | Type          | Notes                        |
|---------------|--------------|------------------------------|
| id            | SERIAL (PK)   |                              |
| user_id       | VARCHAR (FK)   | References users.id          |
| account_type_id| INTEGER (FK)  | References account_types.id  |
| name          | VARCHAR        | e.g. "Chase Checking", "Vanguard 401k" |
| balance       | NUMERIC(14,2)  | Current balance              |
| currency      | VARCHAR(3)     | Default 'GBP'                |
| is_active     | BOOLEAN        | Soft-delete flag             |
| created_at    | TIMESTAMP      |                              |
| updated_at    | TIMESTAMP      |                              |

Index on `(user_id, is_active)`

### liability_types
Predefined categories for liabilities.
| Column  | Type         | Notes                                      |
|--------|-------------|--------------------------------------------|
| id     | SERIAL (PK)  |                                            |
| name   | VARCHAR      | e.g. Mortgage, Student Loan, Credit Card, Auto Loan, Personal Loan, Other |
| user_id| VARCHAR (FK) | NULL = system default, non-NULL = custom   |

`UNIQUE(name, user_id)`

### liabilities
User's liabilities with current balances.
| Column           | Type          | Notes                          |
|-----------------|--------------|--------------------------------|
| id              | SERIAL (PK)   |                                |
| user_id         | VARCHAR (FK)   | References users.id            |
| liability_type_id| INTEGER (FK)  | References liability_types.id  |
| name            | VARCHAR        | e.g. "Home Mortgage", "Visa Card" |
| balance         | NUMERIC(14,2)  | Current outstanding balance    |
| currency        | VARCHAR(3)     | Default 'GBP'                  |
| is_active       | BOOLEAN        | Soft-delete flag               |
| created_at      | TIMESTAMP      |                                |
| updated_at      | TIMESTAMP      |                                |

Index on `(user_id, is_active)`

### snapshots
Point-in-time records of net worth (captured when user updates any balance or manually triggers).
| Column          | Type          | Notes                            |
|----------------|--------------|----------------------------------|
| id             | SERIAL (PK)   |                                  |
| user_id        | VARCHAR (FK)   | References users.id              |
| total_assets   | NUMERIC(14,2)  | Sum of all account balances      |
| total_liabilities | NUMERIC(14,2) | Sum of all liability balances   |
| net_worth      | NUMERIC(14,2)  | assets - liabilities             |
| snapshot_date  | DATE           | Date of snapshot                 |
| detail_json    | JSONB          | Breakdown: each account/liability name + balance at that time |
| created_at     | TIMESTAMP      |                                  |

`UNIQUE(user_id, snapshot_date)` — one snapshot per day, upserted on update.
Index on `(user_id, snapshot_date)`

## Default Seed Data

**Account types:** Checking, Savings, Brokerage, Retirement (401k/IRA), Crypto, Real Estate, Other

**Liability types:** Mortgage, Student Loan, Credit Card, Auto Loan, Personal Loan, Medical Debt, Other

## UI Pages

### Dashboard (`dashboard.py`)
- **Net worth headline number** (large, colored green/red)
- **Assets total** and **Liabilities total** side-by-side
- **Net worth over time** — line chart from snapshots (last 6 months, 1 year, all time toggle)
- **Asset allocation** — pie/donut chart by account type
- **Liability breakdown** — pie/donut chart by liability type
- **Assets vs Liabilities** — stacked bar chart over time

### Accounts (`accounts.py`)
- List all active accounts grouped by type, showing name + balance
- Add new account (type, name, balance)
- Edit balance (updates balance + triggers snapshot)
- Deactivate account

### Liabilities (`liabilities.py`)
- List all active liabilities grouped by type, showing name + balance
- Add new liability (type, name, balance)
- Edit balance (updates balance + triggers snapshot)
- Deactivate liability

### History (`history.py`)
- Table of all snapshots: date, total assets, total liabilities, net worth, change from previous
- Expandable detail showing per-account/liability breakdown at each snapshot
- Export to CSV

## Testing Strategy

### Structure
- One test file per service module (`test_account_service.py`, `test_liability_service.py`, `test_snapshot_service.py`)
- Shared fixtures in `tests/conftest.py`
- Use `@pytest.fixture` over setup/teardown
- Use `@pytest.mark.parametrize` for testing multiple inputs

### Database Testing
- Session-scoped engine fixture, function-scoped session with transaction rollback:

```python
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()

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

### Factory Fixtures
```python
@pytest.fixture
def make_account(db_session):
    def _make(
        *,
        name: str = "Savings",
        balance: Decimal = Decimal("1000"),
        user_id: str = "test-user",
    ) -> Account:
        account = Account(name=name, balance=balance, user_id=user_id)
        db_session.add(account)
        db_session.flush()
        return account
    return _make
```

### Mocking
- Mock Firebase auth calls (`firebase-admin` SDK) — external boundary
- Mock time with `time-machine` for snapshot date tests
- Use real DB sessions for service tests (integration tests)
- Never mock internal functions or SQLModel models

## Implementation Phases

### Phase 1: Foundation
1. Create project directory structure and `__init__.py` files
2. Fix `pyproject.toml`: set `requires-python = ">=3.12"`, add `loguru` and `pydantic-settings` to dependencies, add `[tool.ruff]` and `[tool.pytest.ini_options]` sections
3. Add dev dependencies: `uv add --dev ruff pytest pytest-mock time-machine`
4. Create `.gitignore` (Python defaults + `.env` + `__pycache__`)
5. `app/config.py` — `pydantic-settings` `BaseSettings` class reading `DATABASE_URL`, `FIREBASE_CREDENTIALS_PATH`, `DEBUG` from `.env`
6. `app/database.py` — SQLModel engine + session factory (`create_engine`, `Session`)
7. `app/models.py` — SQLModel models with full type hints: `User`, `AccountType`, `Account`, `LiabilityType`, `Liability`, `Snapshot`
8. `Dockerfile` + `docker-compose.yml` (app + local Postgres)
9. `.env.example`
10. Verify: `docker-compose up`, confirm tables are created

### Phase 2: Backend Services
11. `app/services/account_service.py` — create, list, update balance, deactivate accounts (keyword-only args, type-hinted, loguru logging)
12. `app/services/liability_service.py` — create, list, update balance, deactivate liabilities
13. `app/services/snapshot_service.py` — capture snapshot (compute totals, store breakdown), query history
14. `app/seed.py` — seed default account types and liability types
15. `tests/conftest.py` — shared fixtures: `db_engine`, `db_session` (transaction rollback), factory fixtures (`make_account`, `make_liability`, `make_snapshot`)
16. `tests/test_account_service.py` — tests for account CRUD + edge cases
17. `tests/test_liability_service.py` — tests for liability CRUD + edge cases
18. `tests/test_snapshot_service.py` — tests for snapshot creation, upsert, history queries
19. Run `ruff check` and `ruff format` to verify code quality

### Phase 3: Streamlit UI (hardcoded test user, no auth yet)
20. `frontend/app.py` — entry point with sidebar navigation (Dashboard, Accounts, Liabilities, History)
21. `frontend/pages/accounts.py` — account management UI with balance editing
22. `frontend/pages/liabilities.py` — liability management UI with balance editing
23. `frontend/pages/dashboard.py` — net worth headline, line chart (Plotly), pie charts for asset/liability breakdown, stacked bar
24. `frontend/pages/history.py` — snapshot table with expandable details, CSV export

**Milestone: fully working app locally with fake user.**

### Phase 4: Firebase Authentication
25. Set up Firebase project in GCP Console, enable Email/Password + Google sign-in providers
26. `app/auth.py` — `verify_token()` + `get_or_create_user()` using firebase-admin SDK
27. `frontend/firebase_auth.html` — HTML/JS component using Firebase JS SDK for client-side login
28. `frontend/auth_component.py` — render login UI, capture ID token into `st.session_state`
29. Wire auth gate into `frontend/app.py` — show login if no token, otherwise show app

### Phase 5: Cloud Deployment
30. Create Cloud SQL instance: `gcloud sql instances create finance-db --database-version=POSTGRES_15 --tier=db-f1-micro --region=us-central1`
31. Create database + user in Cloud SQL
32. Build and push Docker image: `gcloud builds submit --tag gcr.io/PROJECT_ID/finance-tracker`
33. Deploy to Cloud Run with Cloud SQL proxy
34. Set env vars (DATABASE_URL with Unix socket path, FIREBASE_CREDENTIALS_PATH)
35. Verify end-to-end in production

## Key Design Decisions
- **Firebase UID as users PK** — avoids mapping table, direct foreign key from all tables
- **Separate type tables with nullable user_id** — NULL = system default visible to all, non-NULL = user custom
- **Daily snapshots with JSONB detail** — captures full breakdown at each point in time without needing to reconstruct from historical balance changes
- **Upsert snapshots per day** — updating balances multiple times in a day overwrites the same snapshot, keeping history clean
- **`SQLModel.metadata.create_all()` for schema** — simple, no migration tool overhead; can add Alembic later if needed
- **No REST API** — unnecessary for Streamlit (server-side Python can call services directly)
- **Plotly for charts** — richer interactivity than Streamlit's built-in charts (hover, zoom, better styling)
- **pydantic-settings for config** — validated, typed settings from `.env` with defaults
- **loguru for logging** — simpler API than stdlib `logging`, structured output
- **Ruff for linting + formatting** — single tool replaces flake8, isort, black
- **Transaction rollback testing** — each test gets a clean DB state without needing to truncate tables
