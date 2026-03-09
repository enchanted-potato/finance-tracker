---
phase: quick-4
plan: 4
subsystem: database, ui
tags: [sqlmodel, streamlit, data_editor, postgresql, liabilities]

# Dependency graph
requires:
  - phase: quick-2
    provides: liabilities CSV upload (now superseded by entry-based model)
provides:
  - LiabilityEntry SQLModel with liability_entries table (date-keyed per type)
  - liability_service with upsert_liability_entry / delete_liability_entry / list_liability_entries
  - capture_snapshot reads liability_entries for the snapshot date
  - liabilities page with st.data_editor inline editing
  - one-shot migration script to create liability_entries and drop liabilities
affects: [snapshot_service, liabilities page, dashboard totals]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "date-keyed liability entries: one row per (user_id, entry_date, liability_type_id)"
    - "st.data_editor with num_rows=dynamic for inline add/edit/delete"
    - "detect deletions by diffing original _id set vs edited _id set in data_editor"

key-files:
  created:
    - scripts/migrate_liabilities.py
  modified:
    - app/models.py
    - app/services/liability_service.py
    - app/services/snapshot_service.py
    - frontend/pages/liabilities.py

key-decisions:
  - "LiabilityEntry uses UniqueConstraint(user_id, entry_date, liability_type_id) — upsert semantics"
  - "capture_snapshot filters LiabilityEntry by entry_date == snapshot_date (not active flag)"
  - "Deletion detection in data_editor: compare original _id set vs edited _id set"

patterns-established:
  - "Liability data is date-keyed: no more named liabilities with a single rolling balance"

requirements-completed: [QUICK-4]

# Metrics
duration: 8min
completed: 2026-03-09
---

# Quick Task 4: Refactor Liabilities to LiabilityEntry Summary

**date-keyed liability_entries table replacing named Liability accounts, with st.data_editor inline UI and per-date snapshot sync**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-09T20:35:05Z
- **Completed:** 2026-03-09T20:43:07Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Replaced the `Liability` model (named account with rolling balance) with `LiabilityEntry` (one row per date/type)
- Rewrote `liability_service.py` with upsert/delete/list for `LiabilityEntry`; kept `list_liability_types`
- Updated `capture_snapshot` to query `LiabilityEntry` filtered by `entry_date == snapshot_date`
- Replaced form-based liabilities UI with `st.data_editor` (Month, Date, Type, Amount); save syncs snapshot for each affected date
- Created `scripts/migrate_liabilities.py` (idempotent: CREATE IF NOT EXISTS + DROP IF EXISTS)

## Task Commits

1. **Task 1: Add LiabilityEntry model, rewrite liability_service, update snapshot_service** - `38db8ee` (feat)
2. **Task 2: Rewrite liabilities page with st.data_editor** - `675ea64` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified
- `app/models.py` - Removed `Liability` class; added `LiabilityEntry` with unique constraint on (user_id, entry_date, liability_type_id)
- `app/services/liability_service.py` - Full replacement: upsert/delete/list for LiabilityEntry + list_liability_types
- `app/services/snapshot_service.py` - Import LiabilityEntry, filter by entry_date, use lb.amount
- `frontend/pages/liabilities.py` - Rewritten with st.data_editor, Save button, per-date snapshot sync
- `scripts/migrate_liabilities.py` - One-shot migration: create liability_entries, drop liabilities

## Decisions Made
- `LiabilityEntry` uses a `UniqueConstraint` on `(user_id, entry_date, liability_type_id)` enabling simple upsert logic
- `capture_snapshot` now filters liability entries by `entry_date == snapshot_date` rather than `is_active` flag
- Deletion in `st.data_editor` is detected by diffing the `_id` set of the original vs edited DataFrame (hidden column pattern)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Migration must be run manually once against the live database:

```bash
docker-compose exec app python scripts/migrate_liabilities.py
```

This creates the `liability_entries` table and drops the old `liabilities` table.

## Next Phase Readiness
- Liabilities page fully functional with date-keyed entries
- Snapshot service correctly pulls liabilities for the snapshot date
- Old `Liability` model and `liabilities` table references fully removed from service/UI code

---
*Phase: quick-4*
*Completed: 2026-03-09*
