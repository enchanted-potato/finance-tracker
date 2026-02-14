# Architecture

**Analysis Date:** 2026-02-14

## Pattern Overview

**Overall:** Service-layer architecture with clean separation between UI (Streamlit) and business logic.

**Key Characteristics:**
- UI layer (Streamlit) calls service functions directly without REST API
- Service layer handles all data operations and business logic
- Domain models defined in SQLModel (SQLAlchemy + Pydantic hybrid)
- Single-user application (hardcoded test user for Phase 3)
- No inter-service dependencies—each service is independently testable

## Layers

**Data Access Layer:**
- Purpose: Database session management and ORM abstraction
- Location: `app/database.py`, `app/models.py`
- Contains: SQLModel table definitions, session factory
- Depends on: SQLAlchemy/SQLModel, PostgreSQL driver (psycopg2)
- Used by: All service layers

**Service Layer:**
- Purpose: Business logic encapsulation—account/liability/snapshot management
- Location: `app/services/`
- Contains: Pure Python functions with docstrings; no Streamlit dependencies
- Depends on: Database layer, models, external libraries (loguru)
- Used by: Frontend pages

**Frontend/UI Layer:**
- Purpose: User-facing Streamlit interface—forms, navigation, visualization
- Location: `frontend/main.py`, `frontend/pages/*.py`
- Contains: Streamlit page render functions, form handling, Plotly charts
- Depends on: Service layer, Streamlit, session state
- Used by: End user (browser)

**Configuration Layer:**
- Purpose: Environment-based settings management
- Location: `app/config.py`
- Contains: Pydantic BaseSettings singleton
- Depends on: pydantic-settings
- Used by: Database initialization

## Data Flow

**Create/Update Account Flow:**

1. User submits form in `frontend/pages/accounts.py`
2. Page calls `account_service.create_account()` with user_id and details
3. Service validates inputs and inserts into `accounts` table via SQLModel
4. Service logs action and returns created Account model
5. Page reruns and displays updated account list via `account_service.list_accounts()`

**Snapshot Capture Flow:**

1. Account or liability balance changes trigger `frontend/pages/accounts.py` or `frontend/pages/liabilities.py`
2. Page calls `snapshot_service.capture_snapshot(user_id)` after balance update
3. Service queries all active accounts and liabilities for the user
4. Service computes totals (total_assets, total_liabilities, net_worth)
5. Service creates detail_json with account/liability breakdown
6. Service upserts Snapshot record (one per user per day via UniqueConstraint)
7. Dashboard page queries snapshots via `snapshot_service.get_snapshot_history()` for charts

**State Management:**
- **Session State (Streamlit):** User ID, selected page, DB initialization flag
- **Database State:** All persistent data; snapshots are point-in-time denormalized views
- **No in-memory cache:** Each page render fetches fresh data from database

## Key Abstractions

**Account & Liability:**
- Purpose: Represent user assets and debts with current balances
- Examples: `app/models.py` (Account, Liability classes)
- Pattern: SQLModel dual-inheritance (SQLAlchemy table + Pydantic validator)
- Foreign key relationships to types and user

**Snapshot:**
- Purpose: Daily point-in-time record of net worth with historical breakdown
- Examples: `app/models.py` (Snapshot class)
- Pattern: Denormalized aggregate—stores totals + JSONB detail array
- Detail JSON preserves account/liability names and balances as of capture date

**Service Functions:**
- Purpose: Stateless business logic callable from both tests and UI
- Examples: `create_account()`, `update_balance()`, `capture_snapshot()`
- Pattern: Pure functions with explicit parameters, docstrings, keyword-only args
- Return: Model instances or lists; raise ValueError for domain logic errors

**Session Factory:**
- Purpose: Context-managed database session per request
- Examples: `get_session()` generator in `app/database.py`
- Pattern: SQLModel Session with automatic rollback on exception

## Entry Points

**Streamlit App Initialization:**
- Location: `frontend/main.py` (run via `streamlit run frontend/main.py`)
- Triggers: User navigates to Streamlit URL
- Responsibilities: Set page config, initialize database, manage sidebar navigation, render page modules

**Table Creation:**
- Location: `main.py` (script file in root)
- Triggers: `python main.py` (one-time setup)
- Responsibilities: Create all database tables via SQLModel.metadata.create_all()

**Seeding Defaults:**
- Location: `app/seed.py`, called from `frontend/main.py` on first app load
- Triggers: Database initialization
- Responsibilities: Insert system-default account and liability types (Savings, Mortgage, etc.)

## Error Handling

**Strategy:** Fail-fast with domain-specific exceptions.

**Patterns:**
- Service functions raise `ValueError` for domain logic failures (e.g., "Account not found", "Deactivated account")
- Streamlit pages catch exceptions and display user-friendly errors via `st.error()`
- Database constraint violations (FK, unique) propagate as SQLAlchemy exceptions
- Logging via `loguru` at info level for audit trail (create, update, delete operations)

## Cross-Cutting Concerns

**Logging:**
- Tool: loguru
- Usage: Every service function logs create/update/delete actions with user_id and entity ID
- Location: `app/services/*.py`

**Validation:**
- Approach: Pydantic models validate type constraints (Decimal precision, string lengths, FK references)
- Place: Model definitions in `app/models.py`
- Examples: Account balance must be Decimal with 14 digits, 2 decimal places

**Authentication:**
- Current: Hardcoded test user (TEST_USER_ID="test-user") in frontend/main.py
- Scope: Single-user application; Firebase auth planned for Phase 4
- User context passed as parameter to all service functions (user_id: str)

**User Isolation:**
- Pattern: All queries filter by user_id (e.g., `Account.user_id == user_id`)
- Enforcement: Database indexes on (user_id, is_active) for performance
- Scope: Accounts, liabilities, types, snapshots all scoped to user

---

*Architecture analysis: 2026-02-14*
