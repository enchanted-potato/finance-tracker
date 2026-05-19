---
phase: 12-data-pages
plan: 03
subsystem: ui
tags: [tanstack-query, react-hook-form, shadcn, data-pages, crud, liabilities]

# Dependency graph
requires:
  - phase: 12-02
    provides: "DataPage<TItem> component, liabilitiesApi with LiabilityTypeResponse, DataPageConfig interface"
provides:
  - "client/src/pages/LiabilitiesPage.tsx — thin DataPage wrapper with liabilitiesConfig (liability_type_id + amount field mapping)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DataPageConfig<TItem> config pattern — LiabilitiesPage is a 25-line wrapper over generic DataPage"
    - "submitEntry field mapping: item_type_id → liability_type_id, balance → amount (liabilities API difference)"

key-files:
  created: []
  modified:
    - client/src/pages/LiabilitiesPage.tsx (replaced Phase 11 stub with DataPage wrapper)
    - client/src/__tests__/LiabilitiesPage.test.tsx (fixed getByText -> getAllByText for dual-occurrence items)

key-decisions:
  - "LiabilitiesPage uses liability_type_id (not account_type_id) and amount (not balance) in submitEntry — critical liabilities API difference from AccountsPage"
  - "LiabilitiesPage.test.tsx updated from getByText to getAllByText — same dual-occurrence pattern as AccountsPage test (items appear in both list and BalanceEntryForm SelectItem mock)"

requirements-completed: [RDAT-04, RDAT-05]

# Metrics
duration: 120s
completed: 2026-05-17
---

# Phase 12 Plan 03: LiabilitiesPage Config Wrapper Summary

**LiabilitiesPage replaces the Phase 11 stub with a 25-line DataPage config wrapper — liability_type_id and amount field mapping are the two critical differences from AccountsPage**

## Performance

- **Duration:** ~2 min (~120s)
- **Started:** 2026-05-17T19:11:00Z
- **Completed:** 2026-05-17T19:13:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Replaced Phase 11 LiabilitiesPage stub with thin DataPage wrapper using liabilitiesConfig
- Correctly maps `item_type_id → liability_type_id` and `balance → amount` in submitEntry (RDAT-04 key difference from AccountsPage)
- Query keys `['liabilities', 'types']` and `['liabilities', 'history']` match API endpoints exactly
- Fixed LiabilitiesPage.test.tsx dual-occurrence issue with `getAllByText` (same pattern as Plan 02 AccountsPage fix)
- LiabilitiesPage tests: 2/2 pass
- Full suite: 26/27 pass (1 remaining failure is PensionPage — Plan 04 scope)
- Build exits 0

## Task Commits

1. **Task 1: LiabilitiesPage config wrapper** — `6a1f37f` (feat)

## Files Created/Modified

- `client/src/pages/LiabilitiesPage.tsx` — replaced Phase 11 stub with thin DataPage wrapper
- `client/src/__tests__/LiabilitiesPage.test.tsx` — fixed getByText -> getAllByText for dual-occurrence

## Decisions Made

- Used `liability_type_id: body.item_type_id` and `amount: body.balance` in submitEntry — liabilities API uses different field names than accounts API
- Updated test from `getByText` to `getAllByText` — Mortgage/Car Loan appears both in the liability list item (`<span>`) and in the BalanceEntryForm SelectItem mock (`<div>`)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] LiabilitiesPage.test.tsx used `getByText` which fails on dual-occurrence**
- **Found during:** Task 1 (test run — GREEN phase)
- **Issue:** `getByText('Mortgage')` throws "Found multiple elements" because Mortgage appears in both the liability list (`<span>Mortgage</span>`) and in the BalanceEntryForm SelectItem mock (`<div>Mortgage</div>`) — same pattern as AccountsPage.test.tsx fixed in Plan 02
- **Fix:** Changed to `getAllByText('Mortgage').length > 0` and `getAllByText('Car Loan').length > 0`
- **Files modified:** `client/src/__tests__/LiabilitiesPage.test.tsx`
- **Commit:** 6a1f37f

## Known Stubs

None — LiabilitiesPage is fully implemented. PensionPage remains as Phase 11 stub — that is Plan 04 responsibility.

## Threat Surface Scan

All threats from the plan's `<threat_model>` are mitigated via inheritance from DataPage (implemented in Plan 02):

| Threat | Mitigation |
|--------|------------|
| T-12-03-01: Negative amount tampering | Inherited: `z.number().nonnegative()` in BalanceEntryForm entrySchema |
| T-12-03-02: XSS via liability type names | Inherited: Standard JSX interpolation only in DataPage |
| T-12-03-03: Delete without confirmation | Inherited: AlertDialog wraps Delete button in DataPage |

No new threat surface introduced.

## Self-Check

### Files Modified
- [x] `client/src/pages/LiabilitiesPage.tsx` — EXISTS (DataPage wrapper with liabilitiesConfig)
- [x] `client/src/__tests__/LiabilitiesPage.test.tsx` — EXISTS (getAllByText fix applied)

### Commits
- [x] Task 1: `6a1f37f` — feat(12-03): LiabilitiesPage config wrapper using DataPage with liabilitiesApi

### Verification
- [x] `grep "DataPage config=" LiabilitiesPage.tsx` — returns hit on line 24
- [x] `grep "liability_type_id: body.item_type_id"` — returns hit on line 16
- [x] `grep "amount: body.balance"` — returns hit on line 18
- [x] `grep "account_type_id"` — no hit (correct)
- [x] `npm run build` — exits 0
- [x] LiabilitiesPage tests: 2/2 pass
- [x] Full suite: 26/27 pass (PensionPage is Plan 04 scope)

## Self-Check: PASSED

---
*Phase: 12-data-pages*
*Completed: 2026-05-17*
