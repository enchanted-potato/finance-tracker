---
phase: quick-5
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - app/models.py
  - app/services/account_service.py
  - app/services/snapshot_service.py
  - frontend/pages/accounts.py
  - frontend/pages/pension.py
  - scripts/migrate_accounts_to_entries.py
autonomous: true
requirements: []

must_haves:
  truths:
    - "Accounts page shows one editable row per account type per date (no named accounts)"
    - "Pension page shows one editable row per pension provider per date (provider is the type name)"
    - "Snapshot picks the latest balance per account type on or before the snapshot date"
    - "History page shows correct asset totals derived from the latest-per-type logic"
    - "Liabilities behaviour is unchanged"
  artifacts:
    - path: "app/models.py"
      provides: "AccountEntry model mirroring LiabilityEntry — unique on (user_id, entry_date, account_type_id)"
    - path: "app/services/account_service.py"
      provides: "upsert/delete/list functions matching LiabilityEntry service pattern"
    - path: "app/services/snapshot_service.py"
      provides: "_latest_account_entries groups by account_type_id, not name"
    - path: "scripts/migrate_accounts_to_entries.py"
      provides: "One-time migration: renames table, adds unique constraint, drops name/is_active columns"
  key_links:
    - from: "frontend/pages/accounts.py"
      to: "account_service.upsert_account_entry"
      via: "Save changes button"
    - from: "app/services/snapshot_service._latest_account_entries"
      to: "AccountEntry.account_type_id"
      via: "GROUP BY account_type_id subquery"
---

<objective>
Refactor accounts to use a type-keyed entry model, matching how liabilities already work.

**The problem today:**
- `Account` is identified by a freeform `name` field ("Barclays Current", "HSBC Savings"). Each named account has multiple date-keyed entries.
- This means you manage a list of named accounts (like a ledger) rather than simply entering "what is my Cash balance today?"
- Snapshot logic groups by `Account.name` to find the latest entry per named account — creating fragile behaviour if names change or are inconsistent.
- `is_active`, `currency`, and `exchange_rate` fields exist but add complexity that doesn't fit the "enter a total per type per date" mental model.

**What the user wants:**
- Enter balances per account type per date — one row per type (e.g., Cash, Stocks, ISA) just like liabilities work (one row per liability type per date).
- Snapshot picks the latest balance per type on or before the snapshot date.
- History displays totals computed from this latest-per-type logic.

**What this refactor does:**
1. Replaces `Account` with `AccountEntry(user_id, entry_date, account_type_id, balance_gbp)` — same pattern as `LiabilityEntry`.
2. Drops `name`, `is_active`, `currency`, `exchange_rate` from the account entry (the type name IS the label).
3. Updates account service, snapshot service, and frontend pages to match the liability pattern.
4. Provides a migration script to alter the existing `accounts` table.

Purpose: Align accounts data entry with the mental model — "what's my total in each category this month?" not "manage a named account list."
Output: Refactored model, service, snapshot logic, and both account/pension pages, plus a migration script.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md

<!-- Key interfaces the executor needs — extracted from existing codebase -->
<interfaces>
<!-- CURRENT Account model (to be replaced) — from app/models.py -->
```python
class Account(SQLModel, table=True):
    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_user_active", "user_id", "is_active"),
        UniqueConstraint("user_id", "name", "entry_date"),
        {"extend_existing": True},
    )
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=128)
    account_type_id: int = Field(foreign_key="account_types.id")
    name: str = Field(max_length=255)
    entry_date: date_type = Field(default_factory=date_type.today)
    balance: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    currency: str = Field(default="GBP", max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1"), max_digits=10, decimal_places=6)
    is_active: bool = Field(default=True)
    created_at / updated_at: datetime
```

<!-- REFERENCE — LiabilityEntry is the target pattern — from app/models.py -->
```python
class LiabilityEntry(SQLModel, table=True):
    __tablename__ = "liability_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_date", "liability_type_id"),
        {"extend_existing": True},
    )
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=128)
    liability_type_id: int = Field(foreign_key="liability_types.id")
    entry_date: date_type = Field()
    amount: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    currency: str = Field(default="GBP", max_length=3)
    created_at / updated_at: datetime
```

<!-- CURRENT snapshot helper to replace — from app/services/snapshot_service.py -->
```python
def _latest_account_entries(session, user_id, as_of):
    # groups by Account.name — WRONG after refactor
    sub = select(Account.name, func.max(Account.entry_date).label("max_date"))
         .where(Account.user_id == user_id, Account.is_active.is_(True), Account.entry_date <= as_of)
         .group_by(Account.name).subquery()
    stmt = select(Account).join(sub, (Account.name == sub.c.name) & ...)
           .where(Account.user_id == user_id, Account.is_active.is_(True))
```

<!-- Pension type detection — keep this pattern from account_service.py -->
```python
PENSION_TYPE_NAME = "Pension"
def _get_pension_type_id(session, user_id) -> int | None:
    statement = select(AccountType).where(
        (AccountType.name == PENSION_TYPE_NAME),
        (AccountType.user_id.is_(None)) | (AccountType.user_id == user_id),
    )
    at = session.exec(statement).first()
    return at.id if at else None
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Replace Account model with AccountEntry and update account service</name>
  <files>app/models.py, app/services/account_service.py</files>
  <action>
**app/models.py** — Replace the `Account` class with `AccountEntry`:

```python
class AccountEntry(SQLModel, table=True):
    """One balance record per (user, date, account_type). Mirrors LiabilityEntry."""

    __tablename__ = "accounts"  # Keep same table name — migration alters it in place
    __table_args__ = (
        UniqueConstraint("user_id", "entry_date", "account_type_id"),
        {"extend_existing": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=128)
    account_type_id: int = Field(foreign_key="account_types.id")
    entry_date: date_type = Field()
    balance: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    created_at: datetime = Field(default=None, sa_column_kwargs={"server_default": sa_text("now()")})
    updated_at: datetime = Field(default=None, sa_column_kwargs={"server_default": sa_text("now()"), "onupdate": sa_text("now()")})
```

Drop: `name`, `currency`, `exchange_rate`, `is_active`. Keep `__tablename__ = "accounts"` so the migration can ALTER the existing table.

**app/services/account_service.py** — Full rewrite to mirror `liability_service.py`:

- Remove all imports/functions using `Account` and replace with `AccountEntry`.
- Remove `create_account`, `update_account`, `update_balance`, `deactivate_account`, `get_account` (these are legacy named-account functions).
- Keep `_get_pension_type_id` and `list_account_types` unchanged.
- New functions (mirror liability service):

```python
def upsert_account_entry(*, session, user_id, account_type_id, entry_date, balance) -> AccountEntry:
    """Insert or update account entry by (user_id, entry_date, account_type_id)."""
    # Same upsert pattern as upsert_liability_entry

def delete_account_entry(*, session, entry_id, user_id) -> date:
    """Hard-delete an account entry. Returns the affected entry_date."""
    # Same as delete_liability_entry

def list_account_entries(*, session, user_id) -> list[AccountEntry]:
    """All entries for a user, newest date first."""
    # order_by entry_date DESC, account_type_id

def list_pension_entries(*, session, user_id) -> list[AccountEntry]:
    """Account entries where account_type_id matches the Pension type."""
    # Filter by pension_type_id

def list_non_pension_entries(*, session, user_id) -> list[AccountEntry]:
    """Account entries where account_type_id does NOT match the Pension type."""
    # Filter out pension_type_id
```

Remove `list_accounts`, `list_pension_accounts`, `list_non_pension_accounts` — replace with `list_account_entries`, `list_pension_entries`, `list_non_pension_entries`.
  </action>
  <verify>python -c "from app.models import AccountEntry, AccountType, LiabilityEntry; from app.services.account_service import upsert_account_entry, delete_account_entry, list_account_entries, list_pension_entries, list_non_pension_entries, list_account_types; print('imports OK')"</verify>
  <done>AccountEntry replaces Account in models.py with (user_id, entry_date, account_type_id) unique constraint. account_service.py exports upsert/delete/list functions matching the liability service pattern. All imports succeed.</done>
</task>

<task type="auto">
  <name>Task 2: Update snapshot service and migration script</name>
  <files>app/services/snapshot_service.py, scripts/migrate_accounts_to_entries.py</files>
  <action>
**app/services/snapshot_service.py** — Update `_latest_account_entries`:

Replace the existing helper (which groups by `Account.name`) with one that groups by `AccountEntry.account_type_id`:

```python
def _latest_account_entries(session: Session, user_id: str, as_of: date) -> list[AccountEntry]:
    """Return the most recent AccountEntry per account type on or before as_of."""
    from sqlalchemy import func

    sub = (
        select(
            AccountEntry.account_type_id,
            func.max(AccountEntry.entry_date).label("max_date"),
        )
        .where(
            AccountEntry.user_id == user_id,
            AccountEntry.entry_date <= as_of,
        )
        .group_by(AccountEntry.account_type_id)
        .subquery()
    )

    stmt = select(AccountEntry).join(
        sub,
        (AccountEntry.account_type_id == sub.c.account_type_id)
        & (AccountEntry.entry_date == sub.c.max_date),
    ).where(AccountEntry.user_id == user_id)

    return list(session.exec(stmt).all())
```

Update `capture_snapshot` to use `AccountEntry`:
- Import `AccountEntry` instead of `Account`.
- Replace `a.balance * a.exchange_rate` with just `a.balance` (no exchange rate in the new model).
- Replace `a.name` in `detail_json["accounts"]` with the account type name (requires looking up `AccountType` by `account_type_id`, similar to how liability type names are looked up).
- The `detail_json` accounts section should include `type_id`, `type_name`, `balance`.
- Remove the `is_active` filter from the subquery (field no longer exists).

Update all other snapshot functions that import or reference `Account` — replace with `AccountEntry`.

Update import line at top: `from app.models import AccountEntry, LiabilityEntry, LiabilityType, Snapshot` and add `AccountType`.

**scripts/migrate_accounts_to_entries.py** — Create new migration script:

```python
"""Migration: refactor accounts table to type-keyed entry model.

Drops: name, currency, exchange_rate, is_active columns.
Adds: UniqueConstraint(user_id, entry_date, account_type_id).
Drops old index ix_accounts_user_active and ix_accounts_user_name_entry_date.
Creates new index ix_accounts_user_type_date.

WARNING: This deletes any rows that would violate the new unique constraint
(duplicate type on same date for same user). Review data first.

Run once against the live database.
"""
from sqlalchemy import text
from app.database import engine


def main():
    with engine.connect() as conn:
        # Drop old indexes
        conn.execute(text("DROP INDEX IF EXISTS ix_accounts_user_active"))
        conn.execute(text("DROP INDEX IF EXISTS ix_accounts_user_name_entry_date"))

        # Drop columns that no longer exist in the model
        conn.execute(text("ALTER TABLE accounts DROP COLUMN IF EXISTS name"))
        conn.execute(text("ALTER TABLE accounts DROP COLUMN IF EXISTS currency"))
        conn.execute(text("ALTER TABLE accounts DROP COLUMN IF EXISTS exchange_rate"))
        conn.execute(text("ALTER TABLE accounts DROP COLUMN IF EXISTS is_active"))

        # Add new unique constraint
        conn.execute(text("""
            ALTER TABLE accounts
            ADD CONSTRAINT uq_accounts_user_date_type
            UNIQUE (user_id, entry_date, account_type_id)
        """))

        # Add new index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_accounts_user_type_date
            ON accounts(user_id, account_type_id, entry_date)
        """))

        conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    main()
```
  </action>
  <verify>python -c "from app.services.snapshot_service import capture_snapshot, _latest_account_entries; from app.models import AccountEntry; print('snapshot imports OK')"</verify>
  <done>snapshot_service._latest_account_entries groups by account_type_id. capture_snapshot uses AccountEntry.balance directly (no exchange_rate multiplication). Migration script exists and is runnable. All imports succeed.</done>
</task>

<task type="auto">
  <name>Task 3: Update accounts and pension frontend pages</name>
  <files>frontend/pages/accounts.py, frontend/pages/pension.py</files>
  <action>
Both pages need to be updated to match the liabilities page pattern (using type as the row identity, not a name field).

**frontend/pages/accounts.py** — Rewrite to mirror liabilities.py:

- Import `list_non_pension_entries`, `list_account_entries`, `upsert_account_entry`, `delete_account_entry`, `list_account_types`.
- Load `entries = list_non_pension_entries(session=session, user_id=user_id)` and account types.
- Summary card: same logic as liabilities — `latest_date = max(e.entry_date for e in entries)`, total from entries on latest_date. Label: "Total Assets (Mar 2026)".
- DataFrame columns: `_id`, `Date`, `Month`, `Type` (selectbox from non-pension type names), `Balance (£)` (NumberColumn).
- Remove `Name`, `Currency`, `Rate (to GBP)` columns entirely.
- `upsert_account_entry` call: `account_type_id=type_name_to_id[type_name]`, `entry_date=entry_date`, `balance=Decimal(str(amount))`.
- Caption: "Edit balances inline. One row per account type per date. Use the checkbox column to delete rows."
- Keep the "Save changes" button pattern and snapshot capture logic identical to liabilities.py.

**frontend/pages/pension.py** — Rewrite to mirror liabilities.py:

- Import `list_pension_entries`, `upsert_account_entry`, `delete_account_entry`.
- Load `entries = list_pension_entries(session=session, user_id=user_id)`.
- Summary card: same pattern, label "Total Pension (Mar 2026)".
- DataFrame columns: `_id`, `Date`, `Month`, `Provider` (TextColumn — but wait: pension entries are keyed by account_type_id which IS "Pension". There is only one pension type. The pension page currently uses a freeform "Provider" name field on Account.name).

  **Decision needed:** With the new model, pension entries are one row per `(entry_date, account_type_id=pension_type_id)`. If there's only one pension type, the user can only enter one pension balance per date. If they have multiple pension providers (e.g., NEST, Aviva), they would need multiple pension account types.

  **Solution:** Create pension sub-types. On the configure page there's already a type system. For pension, treat each pension provider as a separate AccountType with `name` like "Pension - NEST", "Pension - Aviva" — all identified as pension by matching `_get_pension_type_id` pattern. However, that requires a name prefix convention.

  **Simpler solution (implement this):** Pension page uses the same type-keyed entry as accounts, where pension "types" are individual pension providers configured in AccountType. The pension page shows all AccountTypes that the user has tagged as pension. Use a "Provider" selectbox drawn from pension account types.

  Actually the simplest correct approach: The `_get_pension_type_id` currently finds a single "Pension" type. Replace pension page logic: show entries whose `account_type_id` matches ANY account type whose name starts with "Pension" or is categorized as pension.

  **Cleanest approach for now:** Keep exactly one pension type ("Pension"). If the user has multiple providers, they enter the TOTAL pension balance per date (sum of all providers). This matches the "per type per date" mental model perfectly — pension is one type. Update the pension page caption to say "Enter your total pension balance per date."

  DataFrame columns for pension: `_id`, `Date`, `Month`, `Balance (£)`. No Type column (it's always "Pension"). No Provider freeform field.
  - `upsert_account_entry(account_type_id=pension_type_id, entry_date=entry_date, balance=balance)`.
  </action>
  <verify>python -c "import ast, sys; ast.parse(open('frontend/pages/accounts.py').read()); ast.parse(open('frontend/pages/pension.py').read()); print('syntax OK')"</verify>
  <done>accounts.py shows Type + Balance columns (no Name/Currency/Rate). pension.py shows Date + Balance only. Both pages save via upsert_account_entry with account_type_id. Syntax parses without errors.</done>
</task>

</tasks>

<verification>
After all three tasks complete:

1. Run `pytest tests/` — all existing tests pass.
2. Run `python -c "from app.models import AccountEntry; from app.services.account_service import upsert_account_entry, list_non_pension_entries, list_pension_entries; from app.services.snapshot_service import capture_snapshot; print('all imports OK')"`.
3. Start the app locally with `docker-compose up` and verify:
   - Accounts page shows Type + Balance columns, no Name or Currency columns.
   - Pension page shows Date + Balance columns only with a note about entering total pension balance.
   - Liabilities page is unchanged.
   - Adding an account entry and saving triggers a snapshot.
4. Before running against the live database, run `python scripts/migrate_accounts_to_entries.py`.
</verification>

<success_criteria>
- AccountEntry model in models.py: unique on (user_id, entry_date, account_type_id), no name/currency/exchange_rate/is_active fields.
- account_service.py: upsert_account_entry, delete_account_entry, list_account_entries, list_non_pension_entries, list_pension_entries all present and correct.
- snapshot_service._latest_account_entries: groups by account_type_id (not name).
- accounts.py frontend: Type selectbox + Balance number column. No freeform name field.
- pension.py frontend: Date + Balance columns only.
- Migration script at scripts/migrate_accounts_to_entries.py ready to run once against live DB.
- All Python syntax parses cleanly. Imports resolve.
</success_criteria>

<output>
After completion, create `.planning/quick/5-the-way-accounts-liabilities-and-history/5-SUMMARY.md` with what was changed, any decisions made, and the commit hash.
</output>
