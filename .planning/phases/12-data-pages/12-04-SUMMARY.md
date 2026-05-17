---
phase: 12-data-pages
plan: 04
subsystem: ui
tags: [tanstack-query, react-hook-form, shadcn, data-pages, crud, pension]

# Dependency graph
requires:
  - phase: 12-02
    provides: "DataPage, pensionApi, DataPageConfig, shared data components"
provides:
  - "client/src/pages/PensionPage.tsx — thin DataPage wrapper with pensionConfig (account_type_id mapping, itemLabel: provider)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DataPageConfig<PensionTypeResponse> wiring — 20-line config object delegates all CRUD+entry+history to DataPage"
    - "pension submitEntry uses account_type_id (not liability_type_id) — pension entries are AccountEntry with is_pension=true"
    - "getAllByText assertion pattern for items that appear in both list and BalanceEntryForm SelectItem mock"

key-files:
  created: []
  modified:
    - client/src/pages/PensionPage.tsx (replaced Phase 11 stub with DataPage wrapper)
    - client/src/__tests__/PensionPage.test.tsx (fixed getByText → getAllByText for dual-occurrence)

key-decisions:
  - "PensionPage submitEntry maps item_type_id → account_type_id (same as accounts) — pension entries are AccountEntry with is_pension=true, NOT a separate LiabilityEntry"
  - "itemLabel: 'provider' — the UI calls pension providers 'providers', not 'accounts' or 'liabilities'"

requirements-completed: [RDAT-06, RDAT-07]

# Metrics
duration: 480s
completed: 2026-05-17
---

# Phase 12 Plan 04: PensionPage DataPage Wrapper Summary

**PensionPage replaced as a 20-line thin DataPage config wrapper — pensionApi wired with correct account_type_id mapping and 'provider' itemLabel; both RDAT-06 tests pass**

## Performance

- **Duration:** ~8 min (~480s)
- **Started:** 2026-05-17T19:10:00Z
- **Completed:** 2026-05-17T19:18:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- Replaced Phase 11 PensionPage stub (`<h1>Pension</h1>`) with a full DataPage config wrapper
- pensionConfig wires pensionApi.listTypes, getHistory, createType, updateType, deleteType, createEntry
- submitEntry correctly maps `item_type_id → account_type_id` (pension shares AccountEntry infrastructure)
- `itemLabel: 'provider'` gives correct UI text ("Add provider", "Select provider...", "Delete provider?")
- Fixed PensionPage test `getByText` → `getAllByText` for dual-occurrence (same root cause as AccountsPage Plan 02 fix)
- PensionPage tests: 2/2 pass
- Full vitest suite: 26/27 pass (1 remaining failure is LiabilitiesPage — Plan 03 scope)

## Task Commits

1. **Task 1: PensionPage config wrapper** — `2dc8903` (feat)

## Files Created/Modified

- `client/src/pages/PensionPage.tsx` — replaced Phase 11 stub with `<DataPage config={pensionConfig} />`
- `client/src/__tests__/PensionPage.test.tsx` — fixed `getByText('NEST')` → `getAllByText('NEST').length > 0` (dual-occurrence fix)

## Decisions Made

- Pension submitEntry maps `item_type_id → account_type_id` (not `liability_type_id`) — this is per the API contract: pension entries go into the AccountEntry table with `is_pension=True`, not into LiabilityEntry
- Used `itemLabel: 'provider'` — pension providers are distinct from accounts and liabilities in the UI language

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PensionPage test used `getByText` which fails on dual-occurrence**
- **Found during:** Task 1 (test verification)
- **Issue:** `getByText('NEST')` throws "Found multiple elements" because NEST appears in both the provider list (`<span>NEST</span>`) and in the BalanceEntryForm SelectItem mock (`<div>NEST</div>`)
- **Fix:** Changed to `getAllByText('NEST').length > 0` — semantically equivalent but handles multiple DOM matches. Same fix pattern applied to AccountsPage.test.tsx in Plan 02.
- **Files modified:** `client/src/__tests__/PensionPage.test.tsx`
- **Commit:** 2dc8903

## Known Stubs

None — PensionPage is fully implemented via the DataPage abstraction from Plan 02.

## Threat Surface Scan

All threats from the plan's `<threat_model>` are inherited from Plan 02's DataPage implementation:

| Threat | Mitigation |
|--------|------------|
| T-12-04-01: Negative balance tampering | Inherited: `z.number().nonnegative()` in BalanceEntryForm entrySchema (Plan 02) |
| T-12-04-02: XSS via provider names | Inherited: Standard JSX interpolation only in DataPage (Plan 02) |
| T-12-04-03: Delete without confirmation | Inherited: AlertDialog confirmation in DataPage (Plan 02) |
| T-12-04-04: Non-pension entries via /api/pension | Accepted: Server-side validation in Phase 10 API router |

No new threat surface introduced.

## Self-Check

### Files Modified
- [x] `client/src/pages/PensionPage.tsx` — EXISTS (DataPage wrapper)
- [x] `client/src/__tests__/PensionPage.test.tsx` — EXISTS (dual-occurrence fix)

### Verification checks
- [x] `grep "DataPage config=" PensionPage.tsx` — line 24 hit
- [x] `grep "account_type_id" PensionPage.tsx` — line 16 hit
- [x] `grep "itemLabel.*provider" PensionPage.tsx` — line 20 hit
- [x] No `liability_type_id` in PensionPage.tsx
- [x] No `amount: body.balance` in PensionPage.tsx
- [x] `npm run build` exits 0
- [x] `npx vitest run src/__tests__/PensionPage.test.tsx` — 2/2 pass
- [x] Full suite: 26/27 pass (1 failure is LiabilitiesPage — Plan 03 scope, pre-existing)

### Commits
- [x] Task 1: `2dc8903` — feat(12-04): PensionPage DataPage wrapper with pensionApi config

## Self-Check: PASSED

All files exist. Commit present. Build exits 0. PensionPage tests: 2/2 pass. Full suite: 26/27 (LiabilitiesPage remaining failure is Plan 03 scope — not this plan's responsibility).

---
*Phase: 12-data-pages*
*Completed: 2026-05-17*
