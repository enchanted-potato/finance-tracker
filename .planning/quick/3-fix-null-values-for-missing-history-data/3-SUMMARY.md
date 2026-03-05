---
phase: quick-3
plan: 01
subsystem: snapshot-data-integrity
tags: [null-handling, csv-import, plotly, streamlit, sqlmodel]
dependency_graph:
  requires: [quick-2]
  provides: [null-aware-snapshots, gap-rendering-chart, dash-rendering-history]
  affects: [dashboard, history, snapshot_service, models]
tech_stack:
  added: []
  patterns: [nullable-decimal-fields, none-safe-float-conversion, plotly-gap-rendering]
key_files:
  created: []
  modified:
    - app/models.py
    - app/services/snapshot_service.py
    - frontend/pages/dashboard.py
    - frontend/pages/history.py
    - tests/test_snapshot_service.py
decisions:
  - Store NULL (not 0) for total_liabilities and net_worth when CSV has no liabilities column — prevents false zero-line on charts
  - Treat NULL total_assets as Decimal(0) in import_csv_liabilities net_worth calculation — sensible fallback
  - Apply schema change via direct ALTER TABLE (no Alembic configured) to dev DB
metrics:
  duration: 766s
  completed: 2026-03-03
  tasks_completed: 2
  files_modified: 5
---

# Quick Task 3: Fix NULL Values for Missing History Data — Summary

## One-liner

Nullable Snapshot fields (total_assets/total_liabilities/net_worth) with NULL-aware CSV import, Plotly gap-rendering chart, and dash-rendering history table.

## What Was Built

### Task 1: Make Snapshot fields nullable and update import logic

**app/models.py** — Changed three Snapshot numeric fields from `Decimal` (non-null) to `Decimal | None` with `default=None`:
- `total_assets: Decimal | None`
- `total_liabilities: Decimal | None`
- `net_worth: Decimal | None`

**app/services/snapshot_service.py** — Updated `import_csv_snapshots`:
- Single-value CSV (`Date,Value`): now sets `total_liabilities=None`, `net_worth=None` (assets only)
- Assets-only CSV (`Date,Total Assets`): same — no liabilities column means NULL
- Full CSV (`Date,Total Assets,Total Liabilities,Net Worth`): unchanged — stores real Decimal values

Updated `import_csv_liabilities`:
- When `existing.total_assets is None`, treats it as `Decimal("0")` for the net_worth recalculation

`capture_snapshot` unchanged — always computes real Decimal totals from live accounts.

**Database** — Applied `ALTER TABLE snapshots ALTER COLUMN ... DROP NOT NULL` to dev database for all three columns.

### Task 2: Render NULL values as chart gaps and table dashes

**frontend/pages/dashboard.py** — `_render_line_chart`: passes `None` through to Plotly instead of calling `float(None)`. Plotly Scatter traces with `None` in y-list render as gaps (missing points with no connecting line). Also guarded `_net_worth_delta` and headline fallback values against `None`.

**frontend/pages/history.py** — Updated snapshot table loop to display `-` for `None` fields. Updated `_format_change` to return `-` if either current or previous net_worth is `None`. Guarded edit form `number_input` values against `None` (defaults to `0.0`). Updated `_build_csv` to emit empty string instead of `"None"` for null fields.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed stale test_capture_snapshot_no_accounts assertion**
- **Found during:** TDD RED phase for Task 1
- **Issue:** `detail_json == {"accounts": [], "liabilities": []}` failed because quick-1 added `pension_accounts` and `total_pension` keys to detail_json, but the test was never updated
- **Fix:** Changed to check `detail_json["accounts"] == []` and `detail_json["liabilities"] == []` individually (stops checking the full dict shape)
- **Files modified:** tests/test_snapshot_service.py
- **Commit:** 6c98f39

**2. [Rule 2 - Missing guard] Added None guard for headline fallback values in dashboard.py**
- **Found during:** Task 2 implementation
- **Issue:** `total_assets = latest.total_assets` and `total_liabilities = latest.total_liabilities` would assign `None` when the latest snapshot has NULL fields, then `net_worth = total_assets - total_liabilities` would crash
- **Fix:** Added `if latest.total_assets is not None else Decimal("0")` guards
- **Files modified:** frontend/pages/dashboard.py
- **Commit:** 096b69b

**3. [Rule 2 - Missing guard] Added None guard to _net_worth_delta**
- **Found during:** Task 2 implementation
- **Issue:** `delta = current_net_worth - previous` crashes if `previous` is None (snapshots[-2].net_worth)
- **Fix:** Return `None` early if `previous is None`
- **Files modified:** frontend/pages/dashboard.py
- **Commit:** 096b69b

## Test Results

```
79 passed in 0.64s
```

All 79 tests pass. New tests added (6 total for Task 1 TDD):
- `test_capture_snapshot_stores_non_null_values_when_empty`
- `test_import_portfolio_csv` (updated: asserts None for liabilities/net_worth)
- `test_import_single_value_csv_sets_null_liabilities`
- `test_import_assets_only_csv_sets_null_liabilities`
- `test_import_liabilities_when_total_assets_is_null`

## Commits

| Hash | Message |
|------|---------|
| 6c98f39 | test(quick-3): add failing tests for NULL snapshot fields |
| 96b9a07 | feat(quick-3): make Snapshot fields nullable and update import logic |
| 096b69b | feat(quick-3): render NULL snapshot values as chart gaps and table dashes |

## Self-Check: PASSED

- app/models.py: FOUND
- app/services/snapshot_service.py: FOUND
- frontend/pages/dashboard.py: FOUND
- frontend/pages/history.py: FOUND
- tests/test_snapshot_service.py: FOUND
- All 3 commits confirmed in git log
