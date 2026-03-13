---
phase: quick-5
plan: 1
subsystem: accounts
tags: [refactor, model, accounts, pension, snapshot]
completed_date: "2026-03-13"
duration_minutes: 20
tasks_completed: 3
files_modified: 8
key_files:
  modified:
    - app/models.py
    - app/services/account_service.py
    - app/services/snapshot_service.py
    - app/services/type_service.py
    - frontend/pages/accounts.py
    - frontend/pages/pension.py
    - frontend/pages/dashboard.py
    - tests/conftest.py
    - tests/test_account_service.py
    - tests/test_snapshot_service.py
  created:
    - scripts/migrate_accounts_to_entries.py
decisions:
  - "Kept __tablename__='accounts' on AccountEntry to allow in-place ALTER migration without data loss"
  - "Pension page uses single balance entry per date (total pension), matching the type-keyed model — no provider name field"
  - "dashboard._render_pension_bar now labels bars by entry_date (e.g. Mar 2026) instead of account.name"
---

# Quick Task 5: Accounts/Liabilities/History Refactor Summary

**One-liner:** Replaced named Account model with type-keyed AccountEntry (user_id, entry_date, account_type_id) mirroring LiabilityEntry, with in-place table migration script.

## What Was Done

### Task 1: Replace Account model with AccountEntry (commit 1905305)
- Replaced `Account` class in `app/models.py` with `AccountEntry` having unique constraint on `(user_id, entry_date, account_type_id)`
- Dropped `name`, `currency`, `exchange_rate`, `is_active` fields
- Kept `__tablename__ = "accounts"` for in-place migration
- Rewrote `account_service.py` to export `upsert_account_entry`, `delete_account_entry`, `list_account_entries`, `list_pension_entries`, `list_non_pension_entries`, `list_account_types`
- Removed legacy `create_account`, `update_account`, `update_balance`, `deactivate_account`, `list_accounts`, `list_pension_accounts`, `list_non_pension_accounts`

### Task 2: Update snapshot service and create migration script (commit 9f75a20)
- `_latest_account_entries` now groups by `AccountEntry.account_type_id` (was `Account.name`)
- Removed `is_active` filter (field dropped from model)
- `capture_snapshot` uses `a.balance` directly (no `a.balance * a.exchange_rate`)
- `detail_json` accounts section now includes `type_id`, `type_name`, `balance` (no name/currency/exchange_rate)
- Created `scripts/migrate_accounts_to_entries.py` one-time migration

### Task 3: Rewrite accounts and pension frontend pages (commit 79acd4b)
- `accounts.py`: Type selectbox + Balance (£) number column; no Name/Currency/Rate columns
- `pension.py`: Date + Balance (£) columns only; caption notes to enter total pension balance
- Both pages call `upsert_account_entry` with `account_type_id` (no name parameter)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed downstream Account references breaking imports**
- **Found during:** Overall verification (pytest run)
- **Issue:** `app/services/type_service.py`, `frontend/pages/dashboard.py`, `tests/conftest.py`, `tests/test_account_service.py`, `tests/test_snapshot_service.py` all referenced old `Account` model and legacy service functions
- **Fix:** Updated all files to use `AccountEntry` and new service function names
- **Files modified:** type_service.py, dashboard.py, conftest.py, test_account_service.py, test_snapshot_service.py
- **Commit:** b4d5e4e

## Migration Note

Before running against the live database, execute:
```bash
python scripts/migrate_accounts_to_entries.py
```

This script:
1. Drops old indexes (`ix_accounts_user_active`, `ix_accounts_user_name_entry_date`)
2. Drops columns: `name`, `currency`, `exchange_rate`, `is_active`
3. Adds unique constraint `uq_accounts_user_date_type` on `(user_id, entry_date, account_type_id)`
4. Creates new index `ix_accounts_user_type_date`

## Self-Check: PASSED

All files exist and all commits verified.
