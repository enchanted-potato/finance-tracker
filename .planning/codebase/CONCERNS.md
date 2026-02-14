# Codebase Concerns

**Analysis Date:** 2026-02-14

## Security Concerns

**Hardcoded Test User:**
- Issue: `TEST_USER_ID = "test-user"` is hardcoded in production code at `frontend/main.py:12-14`
- Impact: All users see the same hardcoded user ID regardless of login. No real authentication implemented. Single-user limitation not enforced at runtime.
- Current mitigation: Code comment indicates Firebase auth is planned for Phase 4; currently intended for Phase 3 (local development only)
- Recommendations:
  1. Move test user to environment variable (`TEST_USER_ID` env var)
  2. Add authentication guard that requires valid Firebase token before accessing app
  3. Implement user session validation on every page load
  4. Remove hardcoded test user once Firebase auth is integrated

**Missing Firebase Authentication:**
- Issue: Firebase Admin SDK imported in `pyproject.toml` but never initialized or used
- Files: `pyproject.toml:11`, `frontend/main.py` imports not present
- Current mitigation: Single-user deployment model (only one person uses the app)
- Recommendations: Implement Firebase auth in Phase 4 per CLAUDE.md roadmap

**Database Connection String in Settings:**
- Issue: `database_url` loaded from environment in `app/config.py:7` but no validation of format
- Impact: Misconfigured database URLs could silently fail or expose credentials if logged
- Recommendations: Add validation to `Settings` class to ensure database URL is valid PostgreSQL URL format

## Missing Error Handling

**Unvalidated User Input in Batch Updates:**
- Issue: `frontend/pages/accounts.py:142-153` catches `InvalidOperation` for decimal parsing but silently returns errors without rolling back partial updates
- Impact: If user updates 10 accounts and 5 fail, those 5 show errors but the other 5 succeed. Inconsistent state.
- Files: `frontend/pages/accounts.py`, `frontend/pages/liabilities.py` (same pattern in both)
- Recommendations: Wrap batch operations in transactions; either all succeed or all fail

**Generic Exception Catching:**
- Issue: `frontend/pages/configure.py:46` and `147` catch bare `Exception` and display to user
- Impact: Any error (database, disk full, permission denied) shows raw exception string to user; hard to debug
- Files: `frontend/pages/configure.py:46-47`, `frontend/pages/configure.py:147-148`
- Recommendations: Catch specific exceptions (`ValueError`, `IntegrityError`) and provide user-friendly messages

**No Validation on CSV Import Column Detection:**
- Issue: `app/services/snapshot_service.py:155-169` detects CSV columns by case-insensitive header matching but no error if multiple columns match
- Impact: If CSV has both "Value" and "Total Assets", behavior is undefined (first match wins)
- Files: `app/services/snapshot_service.py:177-185`
- Recommendations: Add explicit priority order and warning if ambiguous column names detected

**Unhandled File Encoding Errors:**
- Issue: `frontend/pages/history.py:63` decodes uploaded file as UTF-8 with no fallback encoding
- Impact: Non-UTF-8 CSV files (e.g., Latin-1, Windows-1252) cause silent failures or crashes
- Files: `frontend/pages/history.py:63`
- Recommendations: Try UTF-8 first, fall back to chardet detection, show user-friendly error

## Data Integrity Concerns

**No Transactional Snapshots:**
- Issue: `app/services/snapshot_service.py:12-88` captures snapshot in two steps: fetch data, then insert. Data can change between steps.
- Impact: If user updates account balance while snapshot is being captured, snapshot may have stale data
- Files: `app/services/snapshot_service.py:28-41` (no transaction isolation level set)
- Recommendations: Use `session.begin(nested=True)` or explicit transaction to ensure atomic snapshot capture

**Batch Account Updates Not Atomic:**
- Issue: `frontend/pages/accounts.py:141-161` loops through updates individually without transaction
- Impact: If connection drops mid-update, some accounts updated, others not. App shows success anyway.
- Files: `frontend/pages/accounts.py:140-170`
- Current mitigation: Each individual `update_balance()` commits immediately, so partial state is persisted
- Recommendations: Collect all updates, validate all first, then execute in single transaction

**Decimal Precision Loss in Charts:**
- Issue: `frontend/pages/dashboard.py:112-114` converts `Decimal` to `float` for Plotly charts
- Impact: Precision lost. £10,753.42 → 10753.4199999999 in some cases. Not critical for display but mathematically incorrect for large numbers.
- Files: `frontend/pages/dashboard.py:112-114`
- Recommendations: Keep as Decimal in detail_json; convert only for rendering; use Plotly's string formatting instead of float conversion

**Soft Delete Doesn't Cascade:**
- Issue: `Account.is_active` flag exists but deactivated accounts can still appear in snapshots if detail_json was captured
- Impact: Historical snapshots show accounts that were "deleted". Confusing for users viewing history.
- Files: `app/models.py:48`, `app/services/snapshot_service.py:30-31` (filters by is_active)
- Current mitigation: `capture_snapshot()` filters inactive accounts going forward; old snapshots unchanged
- Recommendations: Document that historical snapshots show accounts as they existed on that date (working as designed)

## Test Coverage Gaps

**No Frontend Page Tests:**
- Issue: All 5 Streamlit pages (`frontend/pages/*.py`) have no tests
- What's not tested: Page rendering, form submission, error display, CSV import flow, snapshot editing
- Files: `frontend/pages/dashboard.py`, `frontend/pages/accounts.py`, `frontend/pages/liabilities.py`, `frontend/pages/history.py`, `frontend/pages/configure.py`
- Risk: Medium - Frontend bugs only caught by manual testing or user reports
- Recommendations:
  1. Use `streamlit.testing.v1` to test page rendering
  2. Test happy path: render page without data, render with data
  3. Test error states: invalid input, database errors

**No Main App Tests:**
- Issue: `frontend/main.py` entry point not tested (sidebar navigation, session state, DB initialization)
- What's not tested: Navigation between pages, database initialization, test user creation, session state management
- Files: `frontend/main.py`
- Risk: Medium - Navigation and initialization bugs only found by manual testing
- Recommendations: Test `_init_db()`, `_ensure_test_user()`, navigation button behavior

**No Integration Tests:**
- Issue: Service layer tests exist but no end-to-end tests (e.g., create account → capture snapshot → verify it appears in history)
- Impact: Cross-service bugs not caught (e.g., if account service changes balance format, snapshot service might break)
- Files: `tests/` directory (only unit tests present)
- Risk: Low - Current codebase is small, but risk increases with growth
- Recommendations: Add integration test suite for critical paths (account lifecycle, snapshot capture)

**Type Service Tests Incomplete:**
- Issue: `tests/test_type_service.py` only tests happy paths; no tests for edge cases
- What's not tested: Renaming to duplicate name, deleting in-use types, boundary conditions
- Files: `tests/test_type_service.py`
- Risk: Low - Errors caught at service layer, but validation logic untested
- Recommendations: Add tests for duplicate detection, foreign key constraints

**No Database Migration Tests:**
- Issue: Schema changes have no test coverage; schema created on first run via `SQLModel.metadata.create_all()`
- Impact: Schema bugs (wrong constraint, missing index) only found on first production run
- Files: `app/models.py`, `frontend/main.py:27`
- Risk: High - Production schema issues hard to debug and fix
- Recommendations: Extract schema into migration scripts (Alembic); test migrations against clean database

**CSV Import Edge Cases Not Covered:**
- Issue: `test_snapshot_service.py` has CSV tests but missing edge cases
- What's not tested:
  - Empty CSV file (header only)
  - CSV with special characters in date/amount fields
  - Very large CSV files (memory/performance)
  - CSV with negative values (should be allowed)
  - CSV with zero-value rows
- Files: `tests/test_snapshot_service.py:152-232`
- Risk: Low - Current tests cover main scenarios; missing edge cases unlikely to break in practice
- Recommendations: Add tests for boundary values, special characters, file size limits

## Fragile Areas

**CSV Date Parsing by Trial and Error:**
- Issue: `app/services/snapshot_service.py:257-264` tries 5 date formats in order until one succeeds
- Why fragile: If a user's data accidentally matches multiple formats, wrong date is parsed. Example: "01/02/2023" matches both "DD/MM/YY" and "MM/DD/YY"
- Safe modification: Document expected date format; add explicit format parameter to import function
- Test coverage: `tests/test_snapshot_service.py:225-232` tests one currency format; should test date format ambiguity

**Detail JSON in Snapshots Can Become Invalid:**
- Issue: `detail_json` in `Snapshot` model is untyped dictionary that can become stale if accounts/liabilities are renamed or deleted
- Why fragile: `frontend/pages/history.py:145-146` reads detail_json assuming structure is valid; if schema changes, breaks
- Safe modification: Define TypedDict for detail_json schema; validate on read; add migration script if schema changes
- Test coverage: No tests verify detail_json structure consistency

**Session Management Scattered Across Pages:**
- Issue: Every page manually calls `get_session()` and closes it. Forgetting `finally` block leaks connections.
- Why fragile: If a developer adds new page and forgets session cleanup, app accumulates open connections
- Files: `frontend/pages/dashboard.py:22-30`, `frontend/pages/accounts.py:27-32`, etc. (pattern repeated 5 times)
- Safe modification: Create context manager wrapper for session; require all pages to use it
- Recommendation: `@contextmanager def get_db_session(): session = next(get_session()); try: yield session; finally: session.close()`

**Streamlit Rerun Side Effects:**
- Issue: Multiple calls to `st.rerun()` can trigger cascading re-renders without explicit user action
- Files: `frontend/pages/accounts.py:70`, `frontend/pages/history.py:78`, `frontend/pages/configure.py:93`, etc.
- Why fragile: User modifies account, page reruns, form clears (clear_on_submit=True), but if user clicks button again too fast, unexpected state
- Risk: Low - Streamlit handles re-render buffering; user would need to click very fast
- Safe modification: Add debouncing on form buttons; document rerun behavior

## Performance Concerns

**No Indexes on Foreign Keys:**
- Issue: `Account.user_id` and `Liability.user_id` have no explicit foreign key indexes
- Impact: Queries like `list_accounts(user_id="x")` do full table scan once database grows
- Files: `app/models.py:43`, `app/models.py:80`
- Current mitigation: Indexes exist on (user_id, is_active) composite; basic user_id lookup uses composite index
- Recommendations:
  1. Add explicit index on `user_id` for list queries (Postgres can use partial index)
  2. Verify composite index covers all query patterns
  3. Run EXPLAIN ANALYZE on slow queries

**Full History Query Not Paginated:**
- Issue: `get_snapshot_history()` returns all snapshots without limit
- Impact: If user has 10 years of daily snapshots (3650 rows), all loaded into memory
- Files: `app/services/snapshot_service.py:91-116`
- Files: `frontend/pages/dashboard.py:28` (requests all history without limit)
- Risk: Low - Current deployment is single-user with limited data; becomes issue at scale
- Recommendations:
  1. Add `limit` and `offset` parameters to `get_snapshot_history()`
  2. Implement pagination in dashboard/history pages
  3. Add test with large dataset

**Pie Chart Recalculation on Every Render:**
- Issue: `frontend/pages/dashboard.py:179-182` and `213-215` rebuild grouped dictionary on every page render
- Impact: Unnecessary computation if page re-renders without data change
- Risk: Low - Currently <10 accounts typical; becomes noticeable at 100+ accounts
- Recommendations: Cache grouped data in Streamlit session state; invalidate only if accounts change

## Configuration & Secrets

**Debug Mode Exposed in Settings:**
- Issue: `app/config.py:9` has `debug: bool = False` which is logged to SQLModel engine
- Impact: If debug=True in production, query logs written to stdout/stderr with sensitive data visible
- Files: `app/config.py:9`, `app/database.py:7`
- Current mitigation: Default is False; only enabled if env var set
- Recommendations: Remove debug flag or restrict logging to structured logs file only

**No Environment Variable Validation:**
- Issue: `app/config.py` does not validate required variables are present
- Impact: Missing `DATABASE_URL` env var causes Pydantic validation error at runtime, not on startup
- Files: `app/config.py:7`
- Recommendations: Add explicit validation in `Settings.__init__` that raises clear errors for missing vars

## Dependencies at Risk

**Firebase Admin SDK Unused:**
- Risk: Dependency bloat; increases attack surface without providing functionality
- Impact: Every deployment includes Firebase auth code not yet used
- Migration plan: Keep in dev dependencies for Phase 4; move to production once auth integrated
- Recommendation: Document Phase 4 implementation plan; add comment in config.py

**Streamlit State Management Fragile:**
- Risk: Streamlit session state is ephemeral; per-browser session only
- Impact: Multi-tab usage problematic (each tab has separate session state); deployed single-user mitigates
- Current mitigation: Single-user deployment; user can only access app from one browser at a time
- Recommendations: Document that app is single-user single-browser; add warning if multiple tabs detected

## Missing Critical Features

**No Data Backup/Export:**
- Problem: User can export snapshots as CSV (history.py) but cannot export full database
- Blocks: User cannot backup full account/liability configuration
- Recommendation: Add "Export Full Data" button that exports JSON with all accounts, liabilities, snapshots

**No Undo/Recovery:**
- Problem: Deleting account type is permanent; no undo available
- Blocks: User cannot recover from accidental deletion
- Recommendation: Add soft-delete for types; implement "Recently Deleted" recovery section

**No Multi-Currency Support:**
- Problem: `currency` field exists in models (Account.currency, Liability.currency) but not enforced or converted
- Blocks: User can have accounts in GBP and USD but net worth calculation treats them identically
- Impact: Net worth calculations incorrect if multiple currencies present
- Recommendations:
  1. Add currency field to Snapshot
  2. Display currency in UI or enforce single currency per user
  3. Or implement proper conversion with exchange rates

**No Data Validation Rules:**
- Problem: User can input negative account balances, zero-balance accounts with liability marked as asset
- Blocks: Data integrity relies on user behavior
- Recommendations: Add business logic validation (e.g., liability balance >= 0, account name not empty)

## Scaling Limits

**Single PostgreSQL Instance:**
- Current capacity: Single free-tier Cloud SQL instance; limited connections and storage
- Limit: App will fail once 3 concurrent users attempt heavy operations
- Scaling path: Upgrade Cloud SQL tier; add connection pooling (PgBouncer)

**Streamlit Deployment Single Instance:**
- Current capacity: One Cloud Run container serving requests
- Limit: ~10 concurrent users before timeouts
- Scaling path: Deploy multiple containers behind load balancer; externalize session state to Redis

**No Database Connection Pooling:**
- Issue: SQLModel creates new connection per request in `get_session()`
- Impact: Connection exhaustion if app scales or has many concurrent users
- Recommendation: Add connection pool via SQLAlchemy pool configuration

---

*Concerns audit: 2026-02-14*
