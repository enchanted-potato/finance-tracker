---
phase: 12-data-pages
plan: 02
subsystem: ui
tags: [tanstack-query, react-hook-form, shadcn, date-fns, zod, vitest, data-pages, crud]

# Dependency graph
requires:
  - phase: 12-01
    provides: "@tanstack/react-query, shadcn dialog/form/calendar/popover/table/label/select, renderWithQuery helper, test stub files"
provides:
  - "client/src/lib/api/accounts.ts — accountsApi with AccountTypeResponse, AccountEntryRequest, HistoryDayResponse types"
  - "client/src/lib/api/liabilities.ts — liabilitiesApi with LiabilityTypeResponse, LiabilityEntryRequest, LiabilityHistoryDayResponse types"
  - "client/src/lib/api/pension.ts — pensionApi with PensionTypeResponse, PensionEntryRequest, PensionHistoryDayResponse types"
  - "client/src/components/data/DataPage.tsx — generic DataPageConfig<TItem> CRUD+entry+history layout"
  - "client/src/components/data/ItemCrudDialog.tsx — form.reset on [open, editItem?.id] pattern"
  - "client/src/components/data/BalanceEntryForm.tsx — date-fns yyyy-MM-dd, nonnegative zod, sonner toasts"
  - "client/src/components/data/HistoryTable.tsx — collapsible React.Fragment rows with expandedDate state"
  - "client/src/pages/AccountsPage.tsx — thin DataPage wrapper with accountsApi config"
  - "client/src/components/ui/alert-dialog.tsx — shadcn AlertDialog for delete confirmation"
  - "sonner installed with Toaster in main.tsx"
affects: [12-03, 12-04]

# Tech tracking
tech-stack:
  added:
    - "sonner@latest (toast notifications)"
    - "shadcn alert-dialog component"
  patterns:
    - "DataPageConfig<TItem> generic config pattern — 3 page files reduce to ~25-line wrappers each"
    - "React.Fragment key pattern for collapsible table rows (parent row + N breakdown rows share a key)"
    - "useEffect keyed on [open, editItem?.id] — stale dialog prevention (not editItem object)"
    - "Zod v4 API: use 'error' key (not 'required_error') for custom validation messages"
    - "react-day-picker v10: 'initialFocus' prop removed — focus handled automatically"

key-files:
  created:
    - client/src/lib/api/accounts.ts
    - client/src/lib/api/liabilities.ts
    - client/src/lib/api/pension.ts
    - client/src/components/data/DataPage.tsx
    - client/src/components/data/ItemCrudDialog.tsx
    - client/src/components/ui/alert-dialog.tsx
  modified:
    - client/src/components/data/BalanceEntryForm.tsx (replaced stub with full implementation)
    - client/src/components/data/HistoryTable.tsx (replaced stub with full implementation)
    - client/src/pages/AccountsPage.tsx (replaced Phase 11 stub with DataPage wrapper)
    - client/src/main.tsx (added Toaster from sonner)
    - client/src/__tests__/AccountsPage.test.tsx (fixed getByText -> getAllByText for dual-occurrence)
    - client/package.json
    - client/package-lock.json

key-decisions:
  - "Zod v4 drops 'required_error' from TypeScript types — must use 'error' key in z.number({ error: ... })"
  - "react-day-picker v10 removes 'initialFocus' prop — removed from Calendar usage, focus is automatic"
  - "sonner was not installed (despite locked Phase 11 decision) — installed and Toaster added to main.tsx"
  - "AccountsPage test used getByText which fails with multiple elements — fixed to getAllByText since ISA appears in both account list and BalanceEntryForm SelectItem mock"
  - "LiabilitiesPage and PensionPage tests remain failing (2/27) — these are Plan 03/04 scope stubs"

requirements-completed: [RDAT-01, RDAT-02, RDAT-03]

# Metrics
duration: 544s
completed: 2026-05-17
---

# Phase 12 Plan 02: Shared Data Components and AccountsPage Summary

**Three typed API modules, four shared `components/data/` components, and a working AccountsPage — the entire Phase 12 component architecture built with TanStack Query, react-hook-form, shadcn Table/Dialog/AlertDialog, and sonner toasts**

## Performance

- **Duration:** ~9 min (~544s)
- **Started:** 2026-05-17T17:51:19Z
- **Completed:** 2026-05-17T18:00:43Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Created 3 typed API modules (accounts, liabilities, pension) matching Phase 10 API contracts exactly
- Installed shadcn alert-dialog and sonner; wired Toaster into main.tsx
- Implemented HistoryTable with collapsible React.Fragment rows (RDAT-03)
- Implemented BalanceEntryForm with date-fns `format(date, 'yyyy-MM-dd')` and `z.number().nonnegative()` (RDAT-02)
- Created ItemCrudDialog with `useEffect` keyed on `[open, editItem?.id]` for stale dialog prevention
- Created generic `DataPage<TItem>` with AlertDialog delete confirmation (security T-12-02-03)
- Replaced AccountsPage stub with thin DataPage config wrapper (RDAT-01)
- All 9 Plan 02 target tests pass (AccountsPage x3, HistoryTable x4, BalanceEntryForm x2)
- All prior passing tests remain passing (25/27 total; 2 failing are Plan 03/04 scope)

## Task Commits

1. **Task 1: API modules and alert-dialog install** — `43f588d` (feat)
2. **Task 2: Shared components, AccountsPage, sonner** — `0d7ef68` (feat)

## Files Created/Modified

- `client/src/lib/api/accounts.ts` — accountsApi with 4 typed interfaces, 6 fetch functions
- `client/src/lib/api/liabilities.ts` — liabilitiesApi with correct `liability_type_id` and `amount` fields
- `client/src/lib/api/pension.ts` — pensionApi with `account_type_id` (reuses accounts pattern)
- `client/src/components/ui/alert-dialog.tsx` — shadcn AlertDialog for delete confirmation
- `client/src/components/data/DataPage.tsx` — generic CRUD+entry+history layout (new file)
- `client/src/components/data/ItemCrudDialog.tsx` — add/edit modal with form reset (new file)
- `client/src/components/data/BalanceEntryForm.tsx` — replaced stub with full implementation
- `client/src/components/data/HistoryTable.tsx` — replaced stub with full implementation
- `client/src/pages/AccountsPage.tsx` — replaced Phase 11 stub with DataPage wrapper
- `client/src/main.tsx` — added Toaster from sonner
- `client/src/__tests__/AccountsPage.test.tsx` — fixed dual-element assertion

## Decisions Made

- Used `z.number({ error: '...' })` instead of `required_error` — Zod v4 type change
- Removed `initialFocus` from Calendar — react-day-picker v10 no longer accepts this prop
- Installed sonner and added Toaster — was a locked Phase 11 decision but not installed yet
- Updated AccountsPage test from `getByText` to `getAllByText` — items appear in both the account list and BalanceEntryForm SelectItem mock rendering

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] sonner package not installed**
- **Found during:** Task 2 (build verification)
- **Issue:** `sonner` was specified as a locked decision from Phase 11 but was not in package.json or node_modules — TypeScript error "Cannot find module 'sonner'"
- **Fix:** `npm install sonner` in client/, added `<Toaster richColors />` to main.tsx
- **Files modified:** client/package.json, client/package-lock.json, client/src/main.tsx
- **Commit:** 0d7ef68

**2. [Rule 1 - Bug] Zod v4 dropped `required_error` from TypeScript types**
- **Found during:** Task 2 (build verification)
- **Issue:** `z.number({ required_error: 'Enter a balance' })` caused TS2353 — property does not exist in Zod v4's type signature. Works at runtime but TypeScript rejects it.
- **Fix:** Changed to `z.number({ error: 'Enter a balance' })` — the Zod v4 equivalent
- **Files modified:** client/src/components/data/BalanceEntryForm.tsx
- **Verification:** `npm run build` exits 0; `z.number().nonnegative()` validates correctly
- **Commit:** 0d7ef68

**3. [Rule 1 - Bug] react-day-picker v10 removed `initialFocus` prop**
- **Found during:** Task 2 (build verification)
- **Issue:** `initialFocus` prop on Calendar caused TS2322 — property does not exist on DayPickerProps in react-day-picker v10. Plan 02 code was written against v8 API; Plan 01 installed v10.
- **Fix:** Removed `initialFocus` from Calendar usage; react-day-picker v10 handles focus automatically
- **Files modified:** client/src/components/data/BalanceEntryForm.tsx
- **Verification:** `npm run build` exits 0; calendar renders correctly
- **Commit:** 0d7ef68

**4. [Rule 1 - Bug] AccountsPage test used `getByText` which fails on dual-occurrence**
- **Found during:** Task 2 (test run)
- **Issue:** `getByText('ISA')` throws "Found multiple elements" because ISA appears in both the account list (`<span>ISA</span>`) and in the BalanceEntryForm SelectItem mock (`<div>ISA</div>`)
- **Fix:** Changed to `getAllByText('ISA').length > 0` — semantically equivalent (ISA is visible) but handles multiple DOM matches
- **Files modified:** client/src/__tests__/AccountsPage.test.tsx
- **Verification:** AccountsPage tests: 3/3 pass
- **Commit:** 0d7ef68

**5. [Rule 1 - Deviation] Cherry-picked Plan 01 commits into worktree branch**
- **Found during:** Worktree setup
- **Issue:** Plan 02 depends on Plan 01 (`depends_on: ["12-01"]`), but this worktree was reset to `c21f945` (pre-Plan 01). The Plan 01 commits lived on `worktree-agent-a82df9dd3a1377ea4`.
- **Fix:** Cherry-picked `fce7429` and `f24d306` (Plan 01 commits) from the other worktree branch into this branch before starting Plan 02 work
- **Verification:** All Plan 01 files present; Plan 02 can build on top

## Known Stubs

None — all files in this plan implement full functionality. LiabilitiesPage and PensionPage remain as Phase 11 stubs — they are Plan 03/04 responsibility, not Plan 02.

## Threat Surface Scan

All threats from the plan's `<threat_model>` are mitigated:

| Threat | File | Mitigation Applied |
|--------|------|--------------------|
| T-12-02-01: Negative balance tampering | BalanceEntryForm.tsx | `z.number().nonnegative()` in entrySchema |
| T-12-02-02: XSS via item.name | DataPage.tsx, HistoryTable.tsx, ItemCrudDialog.tsx | Standard JSX interpolation only; no dangerouslySetInnerHTML |
| T-12-02-03: Delete without confirmation | DataPage.tsx | AlertDialog wraps Delete button — confirmation required |
| T-12-02-04: Stale Firebase token | apiClient.ts | Already mitigated in Phase 11 — no action required |

No new threat surface introduced beyond what the plan's threat model covers.

## Self-Check

### Files Created/Modified
- [x] `client/src/lib/api/accounts.ts` — EXISTS
- [x] `client/src/lib/api/liabilities.ts` — EXISTS
- [x] `client/src/lib/api/pension.ts` — EXISTS
- [x] `client/src/components/ui/alert-dialog.tsx` — EXISTS
- [x] `client/src/components/data/DataPage.tsx` — EXISTS
- [x] `client/src/components/data/ItemCrudDialog.tsx` — EXISTS
- [x] `client/src/components/data/BalanceEntryForm.tsx` — EXISTS (replaced stub)
- [x] `client/src/components/data/HistoryTable.tsx` — EXISTS (replaced stub)
- [x] `client/src/pages/AccountsPage.tsx` — EXISTS (replaced Phase 11 stub)

### Commits
- [x] Task 1: `43f588d` — feat(12-02): API modules for accounts, liabilities, pension and alert-dialog
- [x] Task 2: `0d7ef68` — feat(12-02): shared data components, AccountsPage, and sonner toast integration

## Self-Check: PASSED

All files exist. All commits present. Build exits 0. AccountsPage, HistoryTable, BalanceEntryForm tests: 9/9 pass. Full suite: 25/27 pass (2 remaining failures are Plan 03/04 scope — LiabilitiesPage and PensionPage stubs).

---
*Phase: 12-data-pages*
*Completed: 2026-05-17*
