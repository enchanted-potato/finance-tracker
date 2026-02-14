# Codebase Structure

**Analysis Date:** 2026-02-14

## Directory Layout

```
finance-tracker/
├── app/                    # Python backend: models, services, database
│   ├── __init__.py
│   ├── config.py          # Settings singleton (env var loading)
│   ├── database.py        # SQLModel engine, session factory
│   ├── models.py          # SQLModel table definitions
│   ├── seed.py            # Default data seeding (account/liability types)
│   └── services/          # Business logic (all user-facing functions)
│       ├── __init__.py
│       ├── account_service.py      # Account CRUD + list + balance updates
│       ├── liability_service.py    # Liability CRUD + list + balance updates
│       ├── snapshot_service.py     # Net worth snapshots + history + CSV import
│       └── type_service.py         # Account/liability type management
│
├── frontend/              # Streamlit UI application
│   ├── __init__.py
│   ├── main.py           # App entry point: nav, session init, page routing
│   └── pages/            # Streamlit multi-page layout
│       ├── __init__.py
│       ├── accounts.py    # Asset account management UI
│       ├── liabilities.py # Liability management UI
│       ├── dashboard.py   # Portfolio overview + net worth charts
│       ├── history.py     # Net worth history + CSV export/import
│       └── configure.py   # Account/liability type configuration
│
├── tests/                 # pytest unit tests
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures (DB, models, factories)
│   ├── test_account_service.py        # Account service unit tests
│   ├── test_liability_service.py      # Liability service unit tests
│   ├── test_snapshot_service.py       # Snapshot service unit tests
│   └── test_type_service.py           # Type service unit tests
│
├── main.py                # Script: One-time database table creation
├── pyproject.toml         # uv package manager config + ruff/pytest settings
├── uv.lock                # Locked dependency versions
├── Dockerfile             # Container image for Cloud Run
├── docker-compose.yml     # Local dev: Streamlit + PostgreSQL
├── .env.example           # Template for environment variables
├── .streamlit/            # Streamlit config (theme, server settings)
└── .claude/               # Claude AI instructions and workflows
```

## Directory Purposes

**app/:**
- Purpose: Backend Python package with models and business logic
- Contains: SQLModel ORM models, service layer functions, database session management
- Key files: `models.py` (7 tables), `services/` (4 service modules)

**frontend/:**
- Purpose: Streamlit web UI package
- Contains: Page render functions, form handling, chart visualization, session state management
- Entry point: `frontend/main.py` initializes app config and routes to pages

**tests/:**
- Purpose: Unit test suite using pytest
- Contains: Test cases for all service functions, shared fixtures for DB/factories
- Structure: One test file per service module; fixtures in `conftest.py`

**app/services/:**
- Purpose: Pure business logic isolated from UI
- Contains: Stateless functions for account/liability/snapshot operations
- Exports: No dependencies on Streamlit or UI concerns

**frontend/pages/:**
- Purpose: Individual Streamlit page modules
- Contains: Page-specific UI logic, form validation, error handling
- Pattern: Each module has `render()` function called from main.py

## Key File Locations

**Entry Points:**
- `frontend/main.py`: Streamlit app entry point; start with `streamlit run frontend/main.py`
- `main.py`: One-time setup script; run `python main.py` to create tables

**Configuration:**
- `app/config.py`: Settings singleton loaded from `.env`
- `pyproject.toml`: Python dependencies, ruff/pytest config

**Core Logic:**
- `app/models.py`: 7 SQLModel tables (User, AccountType, Account, LiabilityType, Liability, Snapshot, etc.)
- `app/services/`: 4 modules with pure functions (no Streamlit imports)
  - `account_service.py`: create_account, list_accounts, update_balance, deactivate_account
  - `liability_service.py`: create_liability, list_liabilities, update_balance, deactivate_liability
  - `snapshot_service.py`: capture_snapshot, get_snapshot_history, get_latest_snapshot, import_csv_snapshots
  - `type_service.py`: create/rename/delete account/liability types

**Testing:**
- `tests/conftest.py`: Shared fixtures (db_engine, db_session, test_user, account_type, liability_type, factories)
- `tests/test_*_service.py`: One file per service module with unit tests

**Database:**
- `app/database.py`: SQLModel engine initialization and session generator

## Naming Conventions

**Files:**
- Service modules: `*_service.py` (e.g., `account_service.py`, `snapshot_service.py`)
- Page modules: `{page_name}.py` (e.g., `dashboard.py`, `accounts.py`)
- Test files: `test_{module_name}.py` (e.g., `test_account_service.py`)
- Model file: `models.py` (all SQLModel table classes in one file)

**Functions:**
- Service functions: snake_case (e.g., `create_account`, `list_accounts`, `update_balance`)
- Private helpers: Prefixed with `_` (e.g., `_parse_date()`, `_parse_decimal()`)
- Page render function: `render()` (one per page module)

**Variables:**
- Database session: `session` (SQLModel.Session instance)
- User ID: `user_id` (Firebase UID string)
- Type mapping dicts: `{type_name}_map` (e.g., `account_type_map = {at.id: at.name for at in account_types}`)

**Classes:**
- Model classes: PascalCase (e.g., `Account`, `Liability`, `Snapshot`)
- Exceptions: Raise ValueError for domain logic errors; let SQLAlchemy exceptions propagate

## Where to Add New Code

**New Feature (e.g., budget tracking):**
- Primary code: `app/services/budget_service.py` with pure functions
- Models: Add new table class to `app/models.py` (e.g., Budget, BudgetType)
- UI: Add new page `frontend/pages/budget.py` with `render()` function
- Route: Register page in `frontend/main.py` navigation menu
- Tests: Add `tests/test_budget_service.py` with service function tests

**New Component/Module:**
- Implementation: Follow service layer pattern in `app/services/{domain}_service.py`
- Exports: Only pure functions that accept session parameter
- No Streamlit imports in service layer
- All functions keyword-only arguments (use `*` parameter separator)

**Utilities:**
- Shared helpers: Add to service module as private functions prefixed with `_`
- Common date/number parsing: `snapshot_service.py` has `_parse_date()`, `_parse_decimal()` as examples
- Database utilities: Put in `app/database.py` if used across services

## Special Directories

**frontend/pages/:**
- Purpose: Streamlit multi-page modules
- Generated: No
- Committed: Yes (part of source)
- Pattern: Each page is a separate .py file with `render()` function called from main.py

**tests/:**
- Purpose: Unit test suite
- Generated: No (source files only; __pycache__ generated on run)
- Committed: Yes
- Fixtures: Shared in conftest.py; local to each test file if specific
- Database: Uses separate TEST_DATABASE_URL for isolation

**.streamlit/:**
- Purpose: Streamlit configuration (theme, server settings)
- Generated: No
- Committed: Yes
- Content: config.toml with Streamlit settings (currently minimal)

**.env:**
- Purpose: Runtime environment variables (DATABASE_URL, DEBUG flag)
- Generated: No
- Committed: No (.gitignore excludes)
- Template: `.env.example` shows required variables

## Import Organization

**Service files:**
```python
# Standard library imports
from datetime import date, datetime
from decimal import Decimal

# Third-party imports
from loguru import logger
from sqlmodel import Session, select

# Local imports
from app.models import Account, Liability
```

**Page files:**
```python
# Standard library imports
from datetime import date
from decimal import Decimal

# Third-party imports
import streamlit as st
from sqlmodel import Session

# Local imports
from app.database import get_session
from app.services.account_service import create_account, list_accounts
```

**Pattern:**
1. Standard library (datetime, decimal, os, etc.)
2. Third-party (sqlmodel, streamlit, loguru, plotly, pandas)
3. Local imports (app.models, app.services, app.database)
4. Grouped with blank lines between sections

---

*Structure analysis: 2026-02-14*
