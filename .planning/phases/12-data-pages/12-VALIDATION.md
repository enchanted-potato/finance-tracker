---
phase: 12
slug: data-pages
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-14
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.5 |
| **Config file** | `client/vitest.config.ts` |
| **Quick run command** | `cd client && npx vitest run` |
| **Full suite command** | `cd client && npx vitest run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd client && npx vitest run`
- **After every plan wave:** Run `cd client && npx vitest run`
- **Before `/gsd-verify-work`:** Full suite must be green (all 14+ tests)
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-W0-install | W0 | 0 | RDAT-01–07 | — | N/A | infra | `cd client && npm ls @tanstack/react-query react-hook-form` | ❌ W0 | ⬜ pending |
| 12-W0-shadcn | W0 | 0 | RDAT-01–07 | — | N/A | infra | `ls client/src/components/ui/dialog.tsx client/src/components/ui/form.tsx client/src/components/ui/calendar.tsx` | ❌ W0 | ⬜ pending |
| 12-W0-qcp | W0 | 0 | RDAT-01–07 | — | N/A | unit | `cd client && npx vitest run` | ❌ W0 | ⬜ pending |
| 12-accounts-list | 01+ | 1 | RDAT-01 | — | React JSX escapes user-supplied account names (no XSS) | unit | `cd client && npx vitest run --reporter=verbose src/__tests__/AccountsPage.test.tsx` | ❌ W0 | ⬜ pending |
| 12-accounts-dialog | 01+ | 1 | RDAT-01 | T-XSS | dangerouslySetInnerHTML not used for name display | unit | `cd client && npx vitest run src/__tests__/AccountsPage.test.tsx` | ❌ W0 | ⬜ pending |
| 12-accounts-delete | 01+ | 1 | RDAT-01 | T-repudiation | Delete requires AlertDialog confirmation before calling API | unit | `cd client && npx vitest run src/__tests__/AccountsPage.test.tsx` | ❌ W0 | ⬜ pending |
| 12-balance-date-default | 01+ | 1 | RDAT-02 | — | Date picker defaults to today's date | unit | `cd client && npx vitest run src/__tests__/BalanceEntryForm.test.tsx` | ❌ W0 | ⬜ pending |
| 12-balance-date-submit | 01+ | 1 | RDAT-02 | T-tampering | Negative balance rejected by zod schema before POST | unit | `cd client && npx vitest run src/__tests__/BalanceEntryForm.test.tsx` | ❌ W0 | ⬜ pending |
| 12-history-render | 01+ | 1 | RDAT-03 | — | History table renders daily rows from API response | unit | `cd client && npx vitest run src/__tests__/HistoryTable.test.tsx` | ❌ W0 | ⬜ pending |
| 12-history-expand | 01+ | 1 | RDAT-03 | — | Click on row expands per-account breakdown | unit | `cd client && npx vitest run src/__tests__/HistoryTable.test.tsx` | ❌ W0 | ⬜ pending |
| 12-liabilities-page | 02+ | 2 | RDAT-04, RDAT-05 | — | LiabilitiesPage replicates Accounts CRUD + history pattern | unit | `cd client && npx vitest run src/__tests__/LiabilitiesPage.test.tsx` | ❌ W0 | ⬜ pending |
| 12-pension-page | 03+ | 2 | RDAT-06, RDAT-07 | — | PensionPage replicates Accounts CRUD + history pattern | unit | `cd client && npx vitest run src/__tests__/PensionPage.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `client/src/__tests__/test-utils.tsx` — `renderWithQuery()` helper wrapping QueryClientProvider with retry:false
- [ ] `client/src/__tests__/AccountsPage.test.tsx` — stubs for RDAT-01
- [ ] `client/src/__tests__/BalanceEntryForm.test.tsx` — stubs for RDAT-02
- [ ] `client/src/__tests__/HistoryTable.test.tsx` — stubs for RDAT-03
- [ ] `client/src/__tests__/LiabilitiesPage.test.tsx` — stubs for RDAT-04, RDAT-05
- [ ] `client/src/__tests__/PensionPage.test.tsx` — stubs for RDAT-06, RDAT-07
- [ ] `npm install @tanstack/react-query@5.100.10 date-fns@2` in `client/`
- [ ] `npx shadcn@2.3.0 add dialog form calendar popover table label select` in `client/`
- [ ] `client/src/main.tsx` wrapped with `<QueryClientProvider>`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Balance entry for past date saves snapshot for that date | RDAT-02 | Requires running API (Phase 10); unit tests mock the API | 1. Start docker-compose. 2. Navigate to Accounts page. 3. Select yesterday's date. 4. Submit a balance. 5. Verify history table shows that date. |
| CRUD dialog shows correct values on second open (stale reset) | RDAT-01 | Integration timing — vitest can mock but flaky for dialog remount | 1. Edit account A. 2. Close dialog. 3. Edit account B. 4. Confirm dialog shows B's name, not A's. |
| Collapsible history shows correct per-item breakdown | RDAT-03, RDAT-05, RDAT-07 | Requires real API data from Phase 10 | 1. Enter balances for 2 accounts on same date. 2. Verify history row shows correct total. 3. Expand row to see per-account split. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
