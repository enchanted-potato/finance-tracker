# Coding Conventions

**Analysis Date:** 2026-02-14

## Naming Patterns

**Files:**
- Python modules use snake_case: `account_service.py`, `snapshot_service.py`
- Test files use prefix pattern: `test_account_service.py`, `test_snapshot_service.py`
- Service files grouped in `app/services/` directory by responsibility
- Streamlit page files in `frontend/pages/` with snake_case: `accounts.py`, `dashboard.py`

**Functions:**
- All functions use snake_case: `create_account()`, `list_accounts()`, `update_balance()`
- Service functions are module-level (not in classes)
- Helper/private functions prefixed with underscore: `_parse_date()`, `_parse_decimal()`
- Boolean getters/validators use action verbs: `is_active` (field), `account_type_usage_count()` (function)

**Variables:**
- Local variables use snake_case: `total_assets`, `parsed_date`, `new_balance`
- Constants use UPPER_CASE: `TEST_DATABASE_URL`, `TEST_USER_ID`
- Type union variables named descriptively: `accounts`, `liabilities`, `errors`

**Types and Classes:**
- Model classes use PascalCase: `Account`, `AccountType`, `User`, `Snapshot`
- All models inherit from `SQLModel` (combines SQLAlchemy + Pydantic)
- Settings class: `Settings` in `app/config.py`

## Code Style

**Formatting:**
- Tool: Ruff (Python linter/formatter)
- Line length: 100 characters
- Target version: Python 3.12
- Configuration in `pyproject.toml`:
  ```toml
  [tool.ruff]
  target-version = "py312"
  line-length = 100
  ```

**Linting:**
- Tool: Ruff with rule selections
- Enabled rules: E (errors), F (pyflakes), I (imports), N (naming), UP (upgrades), B (bugbear), SIM (simplification), RUF (ruff-specific)
- Configuration in `pyproject.toml`:
  ```toml
  [tool.ruff.lint]
  select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]
  ```

## Import Organization

**Order:**
1. Standard library imports: `from datetime import date, datetime`, `import csv`, `import io`
2. Third-party imports: `from sqlmodel import Session, select`, `from loguru import logger`
3. Application imports: `from app.models import Account`, `from app.services import ...`

**Path Aliases:**
- No path aliases configured; imports use relative paths from project root
- Streamlit pages import from `app.` directly: `from app.database import engine, get_session`

**Specific patterns:**
- SQLModel queries imported explicitly: `from sqlmodel import Session, select, SQLModel`
- All service functions receive `session: Session` as first parameter
- Logging imported as: `from loguru import logger`
- Configuration imported as singleton: `from app.config import settings`

## Error Handling

**Patterns:**
- Service functions raise `ValueError` for business logic violations
- Error messages include context: `f"Account {account_id} not found for user {user_id}"`
- Examples from `app/services/account_service.py`:
  ```python
  if account is None:
      raise ValueError(f"Account {account_id} not found for user {user_id}")
  if not account.is_active:
      raise ValueError(f"Account {account_id} is deactivated")
  ```
- CSV import returns tuple of (imported, skipped, errors_list) instead of raising
- Decimal parsing wrapped in try-except for `InvalidOperation` and `ValueError`

## Logging

**Framework:** loguru

**Patterns:**
- Import: `from loguru import logger`
- Log successful operations: `logger.info(f"Created account '{name}' (id={account.id}) for user {user_id}")`
- Log state changes: `logger.info(f"Updated account {account_id} balance to {new_balance}")`
- Log bulk operations: `logger.info(f"CSV import for user {user_id}: {imported} imported, {skipped} skipped, {len(errors)} errors")`
- Log on deactivation: `logger.info(f"Deactivated account {account_id}")`
- No debug logging observed; info level used for operational events

## Comments

**When to Comment:**
- Docstrings required for all functions (see JSDoc section)
- Inline comments minimal; code should be self-documenting
- Comments appear in complex logic like CSV import handling (e.g., "Upsert: check if a snapshot already exists for this date")

**JSDoc/TSDoc:**
- All service functions use Google-style docstrings with explicit parameter documentation
- Format in `app/services/account_service.py`:
  ```python
  def create_account(
      *,
      session: Session,
      user_id: str,
      account_type_id: int,
      name: str,
      balance: Decimal = Decimal("0"),
      currency: str = "GBP",
  ) -> Account:
      """Create a new asset account.

      :param session: Database session.
      :param user_id: Firebase UID of the owner.
      :param account_type_id: FK to account_types.
      :param name: Display name for the account.
      :param balance: Initial balance.
      :param currency: ISO 4217 currency code.
      :returns: The newly created account.
      """
  ```
- `:param` for each parameter
- `:returns:` for return value
- `:raises:` documented when function raises exceptions
- Model classes have docstrings: `"""Mirrors Firebase auth user."""`, `"""User asset account with current balance."""`

## Function Design

**Size:** Functions are focused and concise. Longest function is `import_csv_snapshots()` at ~120 lines due to CSV parsing complexity.

**Parameters:**
- Functions use keyword-only arguments (enforce with `*`): `def create_account(*, session, user_id, ...)`
- First parameter is always `session: Session`
- Optional parameters have defaults: `active_only: bool = True`, `snapshot_date: date | None = None`
- Decimal defaults use `Decimal("0")` not `0` to maintain type precision

**Return Values:**
- Single CRUD operations return the model: `-> Account`, `-> Snapshot`
- List operations return typed lists: `-> list[Account]`, `-> list[Snapshot]`
- Query functions return Optional: `-> Account | None`, `-> Snapshot | None`
- Bulk operations return tuple: `tuple[int, int, list[str]]` for (imported, skipped, errors)

## Module Design

**Exports:**
- Services export functions at module level; no classes
- `app/services/__init__.py` file exists but is minimal (no barrel exports observed)
- Streamlit pages import directly from service modules: `from app.services.account_service import create_account, list_accounts`

**Barrel Files:**
- `app/services/__init__.py` is empty (not used for re-exports)
- Consumers import from specific modules directly

## Type Annotations

**Coverage:** Full type annotations throughout
- Function parameters all typed: `session: Session`, `user_id: str`, `balance: Decimal`
- Return types specified: `-> Account`, `-> list[Account] | None`
- Union types use pipe operator: `date | None`, `str | None`
- Decimal used for financial values (not float): `balance: Decimal = Decimal("0")`

---

*Convention analysis: 2026-02-14*
