# Phase 12: Data Pages - Research

**Researched:** 2026-05-14
**Domain:** React CRUD pages with TanStack Query, shadcn/ui dialog + form + table + calendar
**Confidence:** HIGH

---

## Summary

Phase 12 builds three identical data-management pages (Accounts, Liabilities, Pension). Each page has the same pattern: a list of named items with Add/Edit/Delete actions via a dialog, a date-aware balance entry form, and a collapsible entry history table. The API shape is already fully established by Phase 10 (thin-router pattern, float responses, date-grouped history). The React scaffold and Axios client with Firebase token interceptor are in place from Phase 11.

The critical research question is which combination of libraries gives the cleanest implementation for this CRUD-heavy, multi-page pattern. TanStack Query v5 wins over plain `axios+useState` for this use case because it gives automatic refetch-after-mutate, loading/error state management, and request deduplication with zero hand-rolled cache logic. React Hook Form with Zod is worth the small install cost because it provides controlled dialog reset, disabled-state during submit, and inline validation error display — all things you'd re-invent with plain `useState`. For the table, shadcn Table (not TanStack Table) suffices because the history table is non-paginated and non-sortable; TanStack Table adds complexity that this use case doesn't justify.

The three pages are structurally identical. The correct pattern is to build one shared generic `DataPage` compound component (props-driven), then compose each page as a thin wrapper. This avoids tripling the surface area of a bug fix.

**Primary recommendation:** Install `@tanstack/react-query`, `react-hook-form`, `@hookform/resolvers`, `zod`, `date-fns`, and add shadcn components `dialog calendar form popover table label` — all in Wave 0 before writing any page code.

---

## Project Constraints (from CLAUDE.md)

- Stack: React 19.2.5, TypeScript 6.0.2, Vite 8, Tailwind v3.4.19, shadcn/ui 2.3.0 (new-york, dark)
- No REST API hand-rolling — Axios client already wired (`client/src/lib/apiClient.ts`)
- No business logic in React — all computation server-side
- All monetary values are float from the API
- Toasts via `sonner` — NOT `useToast` (confirmed locked decision from Phase 11 research)
- `IS_REACT_ACT_ENVIRONMENT = false` is the global test setup workaround for React 19 in vitest
- Heavy shadcn/Firebase components must be mocked in unit tests (established pattern from Phase 11 tests)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RDAT-01 | Accounts page shows account list with CRUD actions (add/edit/delete) | Dialog component + useQuery for list + useMutation for CUD |
| RDAT-02 | Accounts page allows date-aware balance entry (date picker defaults to today) | shadcn Calendar + Popover as date picker; react-hook-form controlled date field |
| RDAT-03 | Accounts page shows entry history with daily totals and collapsible per-account breakdown | shadcn Table with click-to-expand row pattern; GET /api/accounts/history |
| RDAT-04 | Liabilities page replicates Accounts CRUD + balance entry pattern | Same DataPage abstraction, different apiClient paths |
| RDAT-05 | Liabilities page shows entry history (same pattern as RDAT-03) | Shared history table component, different query key |
| RDAT-06 | Pension page replicates Accounts CRUD + balance entry pattern | Same DataPage abstraction, different apiClient paths |
| RDAT-07 | Pension page shows entry history (same pattern as RDAT-03) | Shared history table component, different query key |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CRUD operations (add/edit/delete items) | API / Backend | — | FastAPI routes own persistence; React fires mutations, API validates and saves |
| Account/liability/pension list rendering | Browser / Client | — | useQuery fetches list; React renders the returned data |
| Dialog form state (controlled open/reset) | Browser / Client | — | Client-side UX concern — Dialog open state + RHF form instance |
| Form validation | Browser / Client | — | Client-side validation only (name required, balance required); no server-round-trip needed for basic field checks |
| Balance entry + date capture | API / Backend | Browser / Client | API owns snapshot creation; client sends {account_type_id, entry_date, balance} |
| Entry history aggregation (daily totals) | API / Backend | — | GET /api/accounts/history returns server-computed totals; React must NOT re-compute |
| Collapsible row expand | Browser / Client | — | Pure UI state: `expandedRow: string | null` in useState |
| Toast notifications | Browser / Client | — | sonner is the confirmed library (locked Phase 11 decision) |
| Currency formatting (display only) | Browser / Client | — | `Intl.NumberFormat` for display; no computation |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-query | 5.100.10 | Server state: useQuery (fetch), useMutation (CUD), automatic cache invalidation | Industry standard for React data fetching; eliminates hand-rolled loading/error state; React 19 support from v5.52.1 |
| react-hook-form | 7.75.0 | Controlled dialog forms with reset, validation, disabled-during-submit | Zero-re-render form control; reset() on dialog close prevents stale values; RHF 7.55+ required for resolvers v5 |
| @hookform/resolvers | 5.2.2 | Zod schema -> RHF resolver bridge | Ships Zod v4 support as of v5.1.0; no separate adapter needed |
| zod | 4.4.3 (already installed) | Form schema validation | Already present as transitive dep; v4 is supported by resolvers 5.2.2 |
| date-fns | 2.30.0 (v2) | Date formatting in calendar trigger button | react-day-picker@8.10.1 (installed by shadcn calendar) requires `date-fns ^2.28.0 || ^3.0.0`; install v2 to avoid dual version |

[VERIFIED: npm registry — all versions confirmed via `npm view`]
[VERIFIED: Context7 /tanstack/query — React 19 peer dep confirmed at v5.52.1+]
[VERIFIED: github.com/react-hook-form/resolvers — Zod v4 support added v5.1.0, fixed v5.2.2]

### Supporting (shadcn/ui components to add in Wave 0)

| Component | Install Command | Purpose | Already Installed? |
|-----------|----------------|---------|-------------------|
| dialog | `npx shadcn@2.3.0 add dialog` | CRUD add/edit modal | No (but @radix-ui/react-dialog already in package.json) |
| form | `npx shadcn@2.3.0 add form` | Form with label + error display; installs @hookform/resolvers + react-hook-form | No |
| calendar | `npx shadcn@2.3.0 add calendar` | Date picker calendar; installs react-day-picker@8.10.1 | No |
| popover | `npx shadcn@2.3.0 add popover` | Wraps calendar in popover trigger | No |
| table | `npx shadcn@2.3.0 add table` | Entry history table | No |
| label | `npx shadcn@2.3.0 add label` | Form labels (required by `form` component) | No |
| select | `npx shadcn@2.3.0 add select` | Account type dropdown in entry form | No |

[VERIFIED: github.com/shadcn-ui/ui@shadcn@2.3.0 registry JSON files — dependency lists confirmed]

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @tanstack/react-query | SWR | SWR is simpler but lacks useMutation (requires manual optimistic/rollback) — TanStack has full mutation lifecycle |
| @tanstack/react-query | plain axios + useState | Requires hand-rolling loading/error state, deduplication, and post-mutation refetch — 3 identical pages means tripling that code |
| @tanstack/react-table (TanStack Table) | shadcn Table (plain HTML) | TanStack Table adds ColumnDef boilerplate for non-paginated, non-sortable data — plain shadcn Table is sufficient |
| react-hook-form + zod | plain controlled inputs | For 2-field forms it's marginal, but controlled dialog reset (form.reset() on Dialog close) and inline error messages justify the install |
| react-day-picker v8 (via shadcn) | native HTML `<input type="date">` | Native date input has no popover UX, looks inconsistent with the dark theme; shadcn Calendar is the established pattern |

**Installation (Wave 0, order matters):**
```bash
cd client

# 1. shadcn components (installs react-day-picker@8.10.1 + radix deps automatically)
npx shadcn@2.3.0 add dialog form calendar popover table label select

# 2. TanStack Query
npm install @tanstack/react-query@5.100.10

# 3. date-fns v2 (required by react-day-picker@8.10.1)
npm install date-fns@2

# Note: react-hook-form and @hookform/resolvers are installed by shadcn form command
```

**Version verification (already run):**
- @tanstack/react-query: 5.100.10 [VERIFIED: npm registry]
- react-hook-form: 7.75.0 [VERIFIED: npm registry]
- @hookform/resolvers: 5.2.2 [VERIFIED: npm registry]
- zod: 4.4.3 already in node_modules [VERIFIED: codebase]
- react-day-picker (via shadcn calendar): 8.10.1 [VERIFIED: github.com/shadcn-ui/ui@shadcn@2.3.0 calendar.json]
- date-fns: 2.30.0 available [VERIFIED: npm registry]

---

## Architecture Patterns

### System Architecture Diagram

```
User action (click Add/Edit/Delete/Submit)
         │
         ▼
React Page Component (AccountsPage/LiabilitiesPage/PensionPage)
         │  wraps
         ▼
DataPage<TItem, TEntry> compound component (shared generic)
         │
         ├──► Item List Section
         │         │  useQuery(['accounts', 'types']) ──► GET /api/accounts/types
         │         │  renders <ItemCard> with Edit/Delete buttons
         │         │
         ├──► CRUD Dialog (Dialog + Form + useMutation)
         │         │  useMutation → POST/PUT/DELETE /api/accounts/*
         │         │  onSuccess: queryClient.invalidateQueries(['accounts', 'types'])
         │         │  onSuccess: toast.success(...)
         │         │
         ├──► Balance Entry Section (Form + Calendar + useMutation)
         │         │  useMutation → POST /api/accounts/entries
         │         │  onSuccess: queryClient.invalidateQueries(['accounts', 'history'])
         │         │
         └──► Entry History Section
                   │  useQuery(['accounts', 'history']) ──► GET /api/accounts/history
                   │  useState(expandedDate) for collapsible rows
                   │  renders <HistoryTable> with click-to-expand
                   ▼
              FastAPI Backend (Phase 10 routes — all business logic here)
```

### Recommended Project Structure

```
client/src/
├── components/
│   ├── ui/                     # shadcn primitives (auto-generated)
│   │   ├── dialog.tsx
│   │   ├── form.tsx
│   │   ├── calendar.tsx
│   │   ├── popover.tsx
│   │   ├── table.tsx
│   │   ├── label.tsx
│   │   └── select.tsx
│   ├── AppLayout.tsx           # existing
│   ├── AppSidebar.tsx          # existing
│   ├── PrivateRoute.tsx        # existing
│   └── data/                  # Phase 12 shared components
│       ├── DataPage.tsx        # generic CRUD+entry+history layout
│       ├── ItemCrudDialog.tsx  # add/edit modal (generic)
│       ├── BalanceEntryForm.tsx# date picker + amount + submit
│       └── HistoryTable.tsx    # collapsible daily history
├── lib/
│   ├── apiClient.ts            # existing (Axios + token interceptor)
│   ├── api/
│   │   ├── accounts.ts         # typed fetch functions for accounts endpoints
│   │   ├── liabilities.ts      # typed fetch functions for liabilities endpoints
│   │   └── pension.ts          # typed fetch functions for pension endpoints
│   └── queryClient.ts          # QueryClient singleton
├── pages/
│   ├── AccountsPage.tsx        # thin wrapper: <DataPage config={accountsConfig} />
│   ├── LiabilitiesPage.tsx     # thin wrapper: <DataPage config={liabilitiesConfig} />
│   └── PensionPage.tsx         # thin wrapper: <DataPage config={pensionConfig} />
└── main.tsx                    # add <QueryClientProvider> here
```

### Pattern 1: QueryClientProvider Setup

Add to `client/src/main.tsx`. The QueryClient singleton lives outside the component tree.

```typescript
// Source: https://github.com/tanstack/query/blob/main/docs/framework/react/reference/QueryClientProvider.md
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,      // 30s before background refetch
      retry: 1,
    },
  },
})

// In main.tsx render():
<QueryClientProvider client={queryClient}>
  <App />
</QueryClientProvider>
```

[VERIFIED: Context7 /tanstack/query — QueryClientProvider.md]

### Pattern 2: useQuery for List Data

```typescript
// Source: https://github.com/tanstack/query/blob/main/docs/framework/react/quick-start.md
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'

// In a page or DataPage component:
const { data: accountTypes = [], isPending, isError } = useQuery({
  queryKey: ['accounts', 'types'],
  queryFn: () => apiClient.get('/api/accounts/types').then(r => r.data),
})
```

**Query key convention for this phase:**
- `['accounts', 'types']` — account type list
- `['accounts', 'history']` — account entry history
- `['liabilities', 'types']` — liability type list
- `['liabilities', 'history']` — liability entry history
- `['pension', 'types']` — pension provider list
- `['pension', 'history']` — pension entry history

### Pattern 3: useMutation + Refetch Pattern

Use `invalidateQueries` in `onSuccess` — NOT optimistic updates. Reason: the API is the source of truth; server-computed totals in history would be wrong if computed client-side for an optimistic update. Refetch-after-mutate is correct for this use case.

```typescript
// Source: https://github.com/tanstack/query/blob/main/docs/framework/react/guides/invalidations-from-mutations.md
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

const queryClient = useQueryClient()

const createMutation = useMutation({
  mutationFn: (body: AccountEntryRequest) =>
    apiClient.post('/api/accounts/entries', body).then(r => r.data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['accounts', 'history'] })
    toast.success('Balance entry saved.')
  },
  onError: () => {
    toast.error('Failed to save entry. Please try again.')
  },
})
```

### Pattern 4: shadcn Dialog with Controlled Open + Form Reset

This is the canonical CRUD dialog pattern. The `open` state is controlled externally (not via DialogTrigger) so the form can be reset when the dialog closes.

```typescript
// Source: https://ui.shadcn.com/docs/components/dialog
// Source: https://github.com/shadcn-ui/ui/blob/shadcn@2.3.0/apps/www/public/registry/...
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'

const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
})

function ItemCrudDialog({ open, onOpenChange, editItem, onSuccess }) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: editItem?.name ?? '' },
  })

  // CRITICAL: reset form when dialog opens with new editItem
  React.useEffect(() => {
    if (open) form.reset({ name: editItem?.name ?? '' })
  }, [open, editItem])

  const mutation = useMutation({ ... })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editItem ? 'Edit' : 'Add'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(data => mutation.mutate(data))}>
          {/* form fields */}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

[VERIFIED: Context7 /llmstxt/ui_shadcn_llms_txt — dialog pattern confirmed]
[VERIFIED: Context7 /shadcn-ui/ui — react-hook-form + zodResolver pattern confirmed]

### Pattern 5: shadcn Date Picker (Popover + Calendar)

shadcn/ui does NOT ship a single `<DatePicker>` component. It is composed from `Popover` + `Calendar`. The Calendar component uses react-day-picker@8.10.1 (installed by `npx shadcn@2.3.0 add calendar`).

```typescript
// Source: https://github.com/shadcn-ui/ui/blob/main/apps/v4/content/docs/components/radix/date-picker.mdx
import { format } from 'date-fns'
import { CalendarIcon } from 'lucide-react'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function DatePickerField({ value, onChange }) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn('w-full justify-start text-left font-normal', !value && 'text-muted-foreground')}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {value ? format(value, 'PPP') : 'Pick a date'}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0">
        <Calendar
          mode="single"
          selected={value}
          onSelect={onChange}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  )
}
```

**Default to today:** `const [date, setDate] = React.useState<Date>(new Date())`

**API serialisation:** Convert Date to ISO string before posting: `entry_date: format(date, 'yyyy-MM-dd')`

[VERIFIED: Context7 /shadcn-ui/ui — Calendar + Popover composition pattern]
[VERIFIED: github.com/shadcn-ui/ui@shadcn@2.3.0 calendar.json — react-day-picker@8.10.1 dependency]

### Pattern 6: Collapsible Table Rows (No TanStack Table Required)

The entry history table needs click-to-expand rows showing per-account breakdown. The shadcn Table (plain HTML `<table>` wrapper) is sufficient. Expanding is pure client UI state.

```typescript
// Source: Context7 /shadcn-ui/ui — table pattern + local state
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

function HistoryTable({ data }: { data: HistoryDayResponse[] }) {
  const [expandedDate, setExpandedDate] = React.useState<string | null>(null)

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead className="text-right">Total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map(day => (
          <React.Fragment key={day.date}>
            <TableRow
              className="cursor-pointer hover:bg-muted/50"
              onClick={() => setExpandedDate(expandedDate === day.date ? null : day.date)}
            >
              <TableCell>{day.date}</TableCell>
              <TableCell className="text-right">
                {new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(day.total)}
              </TableCell>
            </TableRow>
            {expandedDate === day.date && day.entries.map(entry => (
              <TableRow key={entry.entry_id} className="bg-muted/20">
                <TableCell className="pl-8 text-muted-foreground">{entry.type_name}</TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(entry.balance)}
                </TableCell>
              </TableRow>
            ))}
          </React.Fragment>
        ))}
      </TableBody>
    </Table>
  )
}
```

[VERIFIED: Context7 /llmstxt/ui_shadcn_llms_txt — Table component pattern]

### Pattern 7: Generic DataPage Abstraction

Three pages are structurally identical. Build one `DataPage<TItem>` component parameterised by config:

```typescript
interface DataPageConfig<TItem> {
  title: string                            // "Accounts" | "Liabilities" | "Pension"
  queryKey: string[]                       // ['accounts', 'types'] etc.
  historyQueryKey: string[]               // ['accounts', 'history']
  fetchItems: () => Promise<TItem[]>      // apiClient.get('/api/accounts/types').then(r => r.data)
  fetchHistory: () => Promise<HistoryDayResponse[]>
  createItem: (name: string) => Promise<unknown>   // apiClient.post('/api/accounts/types', ...)
  updateItem: (id: number, name: string) => Promise<unknown>
  deleteItem: (id: number) => Promise<unknown>
  submitEntry: (body: EntryRequest) => Promise<unknown>
  itemLabel: string                        // "account" | "liability" | "provider"
}
```

Each page file is then 20-30 lines:
```typescript
// AccountsPage.tsx
const config: DataPageConfig<AccountTypeResponse> = {
  title: 'Accounts',
  queryKey: ['accounts', 'types'],
  historyQueryKey: ['accounts', 'history'],
  fetchItems: () => apiClient.get('/api/accounts/types').then(r => r.data),
  // ... etc
}
export function AccountsPage() { return <DataPage config={config} /> }
```

### Anti-Patterns to Avoid

- **Storing fetched data in useState:** Use `useQuery` only — never copy API data into local state.
- **Stale dialog values:** Always call `form.reset()` inside a `useEffect` keyed on `[open, editItem]` — forgetting this causes the edit dialog to show the previously-edited item's values.
- **Computing history totals in React:** The API returns `total: float` server-computed; never re-sum `entries[]` in the client.
- **Using TanStack Table for the history table:** Adds `ColumnDef` boilerplate for non-paginated, non-sortable data. Plain shadcn Table + `expandedDate` useState is ~40 lines vs ~120 lines.
- **Caching the Firebase token:** apiClient already calls `getIdToken(user)` in the interceptor — never read `auth.currentUser.accessToken` directly in page code.
- **Optimistic updates for history totals:** Server computes the total including exchange rates; optimistic total would require client-side recomputation which is explicitly out of scope.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Loading / error state management | Custom `useState({ loading, error, data })` | useQuery + isPending + isError | useQuery handles deduplication, background refetch, staleTime, React.Suspense compat |
| Post-mutation cache invalidation | manual `fetchData()` call after mutation | `queryClient.invalidateQueries()` in `onSuccess` | invalidateQueries marks queries stale and triggers automatic background refetch |
| Form reset on dialog close | manual `setFieldA('')` calls | `form.reset()` from react-hook-form | Handles nested objects, touched state, and validation errors atomically |
| Date formatting | `date.toISOString().slice(0,10)` | `format(date, 'yyyy-MM-dd')` from date-fns | Timezone-safe; date-fns is already installed by react-day-picker |
| Calendar popup | custom dropdown | shadcn Popover + Calendar | Keyboard nav, accessibility, dark theme consistency |
| Field validation error display | custom error span | RHF `formState.errors` + shadcn FormMessage | Already wired to the form's error state |
| Toast notifications | custom div/timeout | `toast.success()` / `toast.error()` from sonner | Locked decision from Phase 11 |

**Key insight:** For CRUD-heavy UIs, the "accidental complexity" is in managing the lifecycle of mutations and their effect on the cached list — TanStack Query makes this 3 lines (`onSuccess: () => queryClient.invalidateQueries(...)`).

---

## Common Pitfalls

### Pitfall 1: Dialog Form Shows Stale Values on Second Open

**What goes wrong:** User edits item A, closes dialog, opens edit for item B — dialog still shows item A's name.
**Why it happens:** `useForm` initialises defaultValues once at mount; the dialog renders once and stays mounted (shadcn Dialog uses display:none, not unmount by default).
**How to avoid:** Use `useEffect` to call `form.reset({ name: editItem?.name ?? '' })` keyed on `[open, editItem?.id]`. Run this effect every time the dialog opens with a new item.
**Warning signs:** First edit works, second edit shows wrong name.

### Pitfall 2: react-day-picker@8.10.1 React 19 Peer Warning

**What goes wrong:** `npm install` prints peer dependency warning: `react-day-picker@8.10.1 requires react@^18.0.0` — project uses React 19.
**Why it happens:** react-day-picker v8's peerDependencies cap at React 18. React 19 is API-compatible.
**How to avoid:** The component works correctly at runtime — ignore the peer warning or add `--legacy-peer-deps` only for that install. Do NOT upgrade to react-day-picker v9/v10 — the shadcn@2.3.0 calendar component is written for the v8 API and will break on v9 (different props: `mode`, `selected`, `onSelect` → different surface in v9).
**Warning signs:** Build fails or Calendar props show TypeScript errors after accidentally upgrading.

### Pitfall 3: Zod v4 Import Path

**What goes wrong:** `import * as z from 'zod'` works but TypeScript shows type errors when used with `zodResolver`.
**Why it happens:** zod v4 changed some internal type shapes; @hookform/resolvers 5.2.2 fixed this but requires importing from the correct path.
**How to avoid:** Use `import { z } from 'zod'` (named import, not namespace import) and `@hookform/resolvers@5.2.2`. If type errors persist, try `import { z } from 'zod/v4'` (zod v4 exports a compatibility shim at that path).
**Warning signs:** TypeScript error: "Type 'Resolver<input<T>, any, output<T>>' is not assignable to type 'Resolver<output<T>...'"

### Pitfall 4: QueryClientProvider Missing from App Root

**What goes wrong:** `useQuery` throws "No QueryClient set, use QueryClientProvider to set one."
**Why it happens:** `<QueryClientProvider>` must wrap the component that calls `useQuery` — it needs to be added to `client/src/main.tsx`, OUTSIDE the `<App>` component (or wrap `<App>` in App.tsx).
**How to avoid:** Wave 0 task — add `<QueryClientProvider client={queryClient}>` to `main.tsx` before any page code is written.
**Warning signs:** Runtime error on first page load.

### Pitfall 5: invalidateQueries Key Mismatch

**What goes wrong:** Mutation succeeds, toast fires, but the list does not refresh.
**Why it happens:** The `queryKey` passed to `invalidateQueries` does not exactly match the key used in `useQuery`.
**How to avoid:** Define query keys as typed constants in a shared file (`lib/queryKeys.ts`) and import them in both `useQuery` calls and `invalidateQueries` calls.
**Warning signs:** List still shows old data after a successful create/delete.

### Pitfall 6: date-fns v2 vs v3 Format API

**What goes wrong:** `format(date, 'PPP')` throws a TypeError or returns wrong output.
**Why it happens:** date-fns v3 changed some function signatures. react-day-picker@8.10.1 accepts `date-fns ^2.28.0 || ^3.0.0`. If both v2 and v3 are installed (npm may hoist one), the version mismatch causes issues.
**How to avoid:** Install `date-fns@2` explicitly (`npm install date-fns@2`) so npm resolves a single version. The `format` function API is identical between v2 and v3 for the format strings used here.
**Warning signs:** `TypeError: Cannot read properties of undefined (reading 'getMonth')` or wrong locale formatting.

### Pitfall 7: TanStack Query Test Setup (missing QueryClientProvider in tests)

**What goes wrong:** Component tests throw "No QueryClient set" even though the test imports the component.
**Why it happens:** `useQuery` hooks require `QueryClientProvider` in the React tree even in tests.
**How to avoid:** Create a `renderWithQuery(ui)` test helper that wraps the component in a fresh `QueryClientProvider` with a test QueryClient (`new QueryClient({ defaultOptions: { queries: { retry: false } } })`). Disable retries in test client to prevent Jest/Vitest timeouts.
**Warning signs:** Test hangs or throws QueryClient error.

---

## Code Examples

### Complete Balance Entry Form with Date Picker

```typescript
// Source: Context7 /shadcn-ui/ui date-picker + /tanstack/query useMutation
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { format } from 'date-fns'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Form, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'
import { CalendarIcon } from 'lucide-react'
import { apiClient } from '@/lib/apiClient'

const entrySchema = z.object({
  account_type_id: z.number({ required_error: 'Select an account' }),
  entry_date: z.date(),
  balance: z.number({ required_error: 'Enter a balance' }).nonnegative(),
})

type EntryValues = z.infer<typeof entrySchema>

export function BalanceEntryForm({ accountTypes, historyQueryKey }) {
  const queryClient = useQueryClient()
  const form = useForm<EntryValues>({
    resolver: zodResolver(entrySchema),
    defaultValues: { entry_date: new Date(), balance: 0 },
  })

  const mutation = useMutation({
    mutationFn: (values: EntryValues) =>
      apiClient.post('/api/accounts/entries', {
        account_type_id: values.account_type_id,
        entry_date: format(values.entry_date, 'yyyy-MM-dd'),
        balance: values.balance,
      }).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: historyQueryKey })
      toast.success('Balance entry saved.')
      form.reset({ entry_date: new Date(), balance: 0 })
    },
    onError: () => toast.error('Failed to save. Please try again.'),
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(d => mutation.mutate(d))}>
        {/* account_type_id select, entry_date calendar, balance input */}
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving...' : 'Save Entry'}
        </Button>
      </form>
    </Form>
  )
}
```

### Test Helper: renderWithQuery

```typescript
// client/src/__tests__/test-utils.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'

export function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| axios + useState for data fetching | TanStack Query v5 useQuery/useMutation | v5.52+ supports React 19 | Eliminates manual loading/error/refetch lifecycle |
| react-query v4 `useQuery(key, fn)` | react-query v5 `useQuery({ queryKey, queryFn })` | v5.0 (2023) | Object argument syntax only; string key overload removed |
| shadcn/ui useToast | sonner | shadcn confirmed sonner as default (2024) | Locked decision from Phase 11 |
| react-day-picker v7 (DatePicker) | react-day-picker v8 + shadcn Calendar | v8 (2022) | shadcn@2.3.0 uses v8; v9/v10 have breaking prop changes |
| form.register() only | useController / FormField for custom inputs | RHF 7.x | shadcn Form uses FormField + Controller pattern for Calendar and Select |

**Deprecated / outdated:**
- `react-query` (v4 package name): v5 uses `@tanstack/react-query`
- TanStack Query `isLoading`: replaced by `isPending` in v5 (both work but `isPending` is preferred)
- react-day-picker `fromDate`/`toDate` props: renamed in v9; use v8 API only with shadcn@2.3.0

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Phase 10 API routes are fully implemented and accessible at localhost:8000 | Architecture | Phase 12 cannot be tested end-to-end without Phase 10; unit tests with mocked apiClient still work |
| A2 | `sonner` package is already installed in client/ | Don't Hand-Roll | Verified: sonner IS in package.json dependencies from Phase 11 install [VERIFIED: codebase] |

**Notes on A1:** The research confirmed Phase 10 plans exist and establish the API contract. Whether they are fully executed is not verified — the plan files exist but SUMMARY files may or may not confirm completion. Unit tests with mocked axios will work regardless.

---

## Open Questions

1. **Account CRUD vs. Account Type CRUD**
   - What we know: The API exposes `/api/accounts/types` (CRUD for account types, e.g. "ISA", "Checking") and `/api/accounts/entries` (balance entries against a type). The "account list" in the UI is actually the list of account types.
   - What's unclear: Does the UI need to show both the type (ISA) AND the current/latest balance in the list? Or just the type names?
   - Recommendation: Research the API schema from Phase 10 Plan 01 — `GET /api/accounts/types` returns `{id, name, is_pension, in_use}` only — no balance. The balance lives in entries. The list page shows types; the entry form selects a type to submit a balance. This is confirmed by the Phase 10 router code.

2. **Currency display**
   - What we know: All monetary values are float. The existing Streamlit app used GBP formatting.
   - What's unclear: Should the currency symbol be hardcoded as GBP or read from entry.currency?
   - Recommendation: Hardcode `Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' })` for Phase 12. Multi-currency display is out of scope per REQUIREMENTS.md.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | npm installs | ✓ | (via nvm/system) | — |
| npm | package installs | ✓ | (current) | — |
| @tanstack/react-query | Data fetching | ✗ (not yet installed) | 5.100.10 available | none — must install |
| react-hook-form | Forms | ✗ (not yet installed) | 7.75.0 available | none — must install |
| @hookform/resolvers | Form validation | ✗ (not yet installed) | 5.2.2 available | none — must install |
| date-fns | Date formatting | ✗ (not yet installed) | 2.30.0 available | none — must install |
| zod | Schema validation | ✓ (already in node_modules) | 4.4.3 | — |
| react-day-picker | Calendar (via shadcn) | ✗ (installed by shadcn add calendar) | 8.10.1 pinned | none — shadcn manages |
| shadcn dialog | CRUD modal | ✗ (not yet added) | via shadcn@2.3.0 | none — must add |
| shadcn form | Form wrapper | ✗ (not yet added) | via shadcn@2.3.0 | none — must add |
| shadcn calendar | Date picker | ✗ (not yet added) | via shadcn@2.3.0 | none — must add |
| shadcn popover | Calendar wrapper | ✗ (not yet added) | via shadcn@2.3.0 | none — must add |
| shadcn table | History table | ✗ (not yet added) | via shadcn@2.3.0 | none — must add |
| shadcn select | Account type dropdown | ✗ (not yet added) | via shadcn@2.3.0 | none — must add |
| shadcn label | Form label | ✗ (not yet added) | via shadcn@2.3.0 | none — must add |
| FastAPI backend | API calls | ✓ (Phase 9 complete) | running on :8000 | — |

**Missing dependencies with no fallback (must be installed in Wave 0):**
- @tanstack/react-query, react-hook-form, @hookform/resolvers, date-fns
- shadcn components: dialog, form, calendar, popover, table, label, select

**Missing dependencies with fallback:**
- None — all required packages have npm registry availability confirmed.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.5 |
| Config file | `client/vitest.config.ts` |
| Quick run command | `cd client && npx vitest run` |
| Full suite command | `cd client && npx vitest run` |
| Current passing tests | 14/14 (3 test files) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RDAT-01 | AccountsPage renders type list from API | unit | `cd client && npx vitest run --reporter=verbose src/__tests__/AccountsPage.test.tsx` | ❌ Wave 0 |
| RDAT-01 | Add dialog opens, submits, closes | unit | same file | ❌ Wave 0 |
| RDAT-01 | Delete confirms and calls API | unit | same file | ❌ Wave 0 |
| RDAT-02 | Date picker defaults to today | unit | `cd client && npx vitest run src/__tests__/BalanceEntryForm.test.tsx` | ❌ Wave 0 |
| RDAT-02 | Submit sends correct ISO date | unit | same file | ❌ Wave 0 |
| RDAT-03 | History table renders rows | unit | `cd client && npx vitest run src/__tests__/HistoryTable.test.tsx` | ❌ Wave 0 |
| RDAT-03 | Click row expands breakdown | unit | same file | ❌ Wave 0 |
| RDAT-04,05 | LiabilitiesPage identical pattern | unit | `cd client && npx vitest run src/__tests__/LiabilitiesPage.test.tsx` | ❌ Wave 0 |
| RDAT-06,07 | PensionPage identical pattern | unit | `cd client && npx vitest run src/__tests__/PensionPage.test.tsx` | ❌ Wave 0 |

**Note on test approach:** Unit tests for data pages mock the apiClient (axios-mock-adapter already installed) and use `renderWithQuery()` helper. They do NOT require a running backend. Full E2E is done manually against the running docker-compose stack.

### Sampling Rate

- **Per task commit:** `cd client && npx vitest run`
- **Per wave merge:** `cd client && npx vitest run` (all 14+ tests green)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `client/src/__tests__/AccountsPage.test.tsx` — covers RDAT-01
- [ ] `client/src/__tests__/BalanceEntryForm.test.tsx` — covers RDAT-02
- [ ] `client/src/__tests__/HistoryTable.test.tsx` — covers RDAT-03
- [ ] `client/src/__tests__/LiabilitiesPage.test.tsx` — covers RDAT-04, RDAT-05
- [ ] `client/src/__tests__/PensionPage.test.tsx` — covers RDAT-06, RDAT-07
- [ ] `client/src/__tests__/test-utils.tsx` — renderWithQuery helper
- [ ] All shadcn components added: dialog, form, calendar, popover, table, label, select
- [ ] npm packages installed: @tanstack/react-query, react-hook-form, @hookform/resolvers, date-fns@2
- [ ] `client/src/main.tsx` updated with QueryClientProvider

**Test mocking strategy (established from Phase 11):**
- Mock `@/lib/apiClient` via `vi.mock('@/lib/apiClient', ...)` — returns a mock axios instance
- Mock `firebase/auth` and `firebase/app` via vitest.config.ts aliases (already configured)
- Mock heavy shadcn components (Calendar, Dialog) that use Radix UI portals with lightweight stubs
- Use `axios-mock-adapter` (already installed) for apiClient response mocking

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Auth is Phase 11 concern; pages require auth via PrivateRoute |
| V3 Session Management | no | Token refresh handled by apiClient interceptor (Phase 11) |
| V4 Access Control | partial | Single-user app; no row-level auth needed in React; API enforces user_id |
| V5 Input Validation | yes | zod schema validates name (non-empty string) and balance (non-negative number) before POST |
| V6 Cryptography | no | Not applicable |

### Known Threat Patterns for CRUD React Pages

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Submitting negative balance values | Tampering | zod `z.number().nonnegative()` on balance field client-side; API validates server-side |
| XSS via account name display | Tampering | React JSX escapes by default; never use `dangerouslySetInnerHTML` for user-supplied names |
| Clicking delete without confirmation | Repudiation | Use AlertDialog (shadcn) for destructive delete to require explicit confirmation |
| Stale token on mutation | Elevation | apiClient interceptor calls `getIdToken(user)` fresh on every request — no stale token risk |

---

## Sources

### Primary (HIGH confidence)

- Context7 `/tanstack/query` — useQuery, useMutation, invalidateQueries, QueryClientProvider docs
- Context7 `/shadcn-ui/ui` — dialog, form, calendar, date-picker, table component patterns
- Context7 `/llmstxt/ui_shadcn_llms_txt` — sonner toast, dialog composition, table rendering
- `github.com/shadcn-ui/ui@shadcn@2.3.0` calendar.json — react-day-picker@8.10.1 dependency [VERIFIED via WebFetch]
- `github.com/shadcn-ui/ui@shadcn@2.3.0` form.json — react-hook-form + @hookform/resolvers + zod deps [VERIFIED via WebFetch]
- npm registry — all package versions verified via `npm view` [VERIFIED: bash commands]
- Codebase — `client/package.json`, `client/src/lib/apiClient.ts`, `client/vitest.config.ts` [VERIFIED: Read]

### Secondary (MEDIUM confidence)

- `github.com/react-hook-form/resolvers/releases` — Zod v4 support confirmed in v5.1.0, type fix in v5.2.2 [VERIFIED via WebFetch]
- WebSearch results on @hookform/resolvers Zod v4 compatibility issues — active thread confirms workaround (`import { z } from 'zod/v4'`) exists

### Tertiary (LOW confidence)

- None — all critical claims are PRIMARY or SECONDARY verified.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions confirmed via npm view and codebase grep
- Architecture: HIGH — API shape confirmed from Phase 10 plan files; TanStack Query pattern from Context7
- Pitfalls: MEDIUM/HIGH — dialog reset and peer warnings verified from official sources; Zod v4 type issue verified from resolver GitHub releases

**Research date:** 2026-05-14
**Valid until:** 2026-06-14 (30 days; packages are stable; react-day-picker v8 is not changing)
