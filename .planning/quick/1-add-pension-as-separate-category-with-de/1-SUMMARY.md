---
phase: quick-1-pension
plan: 01
subsystem: accounts, dashboard, navigation
tags: [pension, dashboard, accounts, snapshot]
dependency_graph:
  requires: []
  provides:
    - list_pension_accounts
    - list_non_pension_accounts
    - _get_pension_type_id
    - pension page UI
  affects:
    - dashboard (4-column metrics, pension bar chart)
    - accounts page (pension excluded from list and add form)
    - snapshot_service (pension excluded from total_assets/net_worth)
tech_stack:
  added: []
  patterns:
    - Pension split via PENSION_TYPE_NAME constant + _get_pension_type_id lookup
    - detail_json extended with pension_accounts and total_pension keys (no DB migration)
key_files:
  created:
    - frontend/pages/pension.py
  modified:
    - app/services/account_service.py
    - app/services/snapshot_service.py
    - frontend/pages/dashboard.py
    - frontend/pages/accounts.py
    - frontend/main.py
decisions:
  - Store total_pension in detail_json (not as a new Snapshot column) to avoid DB migration
  - Pension excluded from total_assets/net_worth in both live dashboard and snapshot captures
  - Pension page mirrors accounts.py pattern for consistency
  - Accounts page filters Pension type from add form and list to prevent accidental use
metrics:
  duration: 697s
  completed: 2026-03-01
  tasks_completed: 2
  files_changed: 6
---

# Quick Task 1: Add Pension as Separate Category — Summary

**One-liner:** Pension split from liquid assets via dedicated service helpers, excluded from Total Assets/Net Worth, visible as 4th dashboard metric and bar chart, with its own management page.

## What Was Built

### Task 1: Service layer
- `_get_pension_type_id(session, user_id)` — looks up the system "Pension" AccountType id
- `list_pension_accounts(session, user_id, active_only)` — returns only Pension-typed accounts
- `list_non_pension_accounts(session, user_id, active_only)` — returns all accounts except Pension
- `capture_snapshot` updated: splits all_accounts into pension/non_pension lists; `total_assets` and `net_worth` exclude pension; `detail_json` gains `pension_accounts` list and `total_pension` string key

### Task 2: UI and navigation
- `frontend/pages/pension.py` — new page: add pension provider, batch update balances, deactivate providers, total metric at bottom
- `frontend/pages/dashboard.py` — 4th column "Total Pension" metric added; pension bar chart (`_render_pension_bar`) rendered at bottom when pension accounts exist; uses `list_non_pension_accounts` and `list_pension_accounts`
- `frontend/main.py` — "Pension" (🏦) nav item added between Liabilities and History; routes to `pension.render()`
- `frontend/pages/accounts.py` — uses `list_non_pension_accounts`; Pension filtered from add-account type selectbox

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 4194ef8 | Service layer — pension helpers and snapshot exclusion |
| 2 | 7ed7004 | Dashboard updates, pension page, and navigation wiring |

## Decisions Made

- **No DB migration needed** — `total_pension` stored in `detail_json` as a string key rather than adding a new Snapshot column. Keeps schema stable.
- **Pension page mirrors accounts.py** — same session/form/rerun pattern for UX consistency.
- **Pension filtered at service level** — `list_non_pension_accounts` filters by type_id so dashboard total_assets is correct even without explicit exclusion in UI code.

## Deviations from Plan

None — plan executed exactly as written.

## Notes

- Pre-existing test suite failure (conftest imports removed `User` model from Phase 5) is out of scope and unrelated to this quick task.

## Self-Check

- [x] `frontend/pages/pension.py` exists
- [x] `app/services/account_service.py` contains `list_pension_accounts`, `list_non_pension_accounts`, `_get_pension_type_id`
- [x] `app/services/snapshot_service.py` updated to exclude pension from totals
- [x] `frontend/pages/dashboard.py` updated with 4 metrics and pension bar chart
- [x] `frontend/pages/accounts.py` updated to exclude pension
- [x] `frontend/main.py` updated with Pension nav and routing
- [x] Commits 4194ef8 and 7ed7004 exist

## Self-Check: PASSED
