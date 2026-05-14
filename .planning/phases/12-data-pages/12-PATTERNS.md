# Phase 12: Data Pages - Pattern Map

**Mapped:** 2026-05-14
**Files analyzed:** 15 (new/modified files)
**Analogs found:** 12 / 15

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `client/src/lib/queryClient.ts` | utility | — | `client/src/lib/firebase.ts` | role-match (singleton module) |
| `client/src/main.tsx` | config | — | `client/src/main.tsx` (existing, modify) | exact (self) |
| `client/src/lib/api/accounts.ts` | service | request-response | `client/src/lib/apiClient.ts` | role-match |
| `client/src/lib/api/liabilities.ts` | service | request-response | `client/src/lib/apiClient.ts` | role-match |
| `client/src/lib/api/pension.ts` | service | request-response | `client/src/lib/apiClient.ts` | role-match |
| `client/src/components/data/DataPage.tsx` | component | CRUD | `client/src/components/AppLayout.tsx` | role-match |
| `client/src/components/data/ItemCrudDialog.tsx` | component | CRUD | `client/src/pages/LoginPage.tsx` | role-match (form + async submit) |
| `client/src/components/data/BalanceEntryForm.tsx` | component | CRUD | `client/src/pages/LoginPage.tsx` | role-match (form + async submit) |
| `client/src/components/data/HistoryTable.tsx` | component | request-response | `client/src/components/AppSidebar.tsx` | role-match (list render) |
| `client/src/pages/AccountsPage.tsx` | component | CRUD | `client/src/pages/AccountsPage.tsx` (existing stub) | exact (self, expand) |
| `client/src/pages/LiabilitiesPage.tsx` | component | CRUD | `client/src/pages/AccountsPage.tsx` | exact (same pattern) |
| `client/src/pages/PensionPage.tsx` | component | CRUD | `client/src/pages/AccountsPage.tsx` | exact (same pattern) |
| `client/src/__tests__/test-utils.tsx` | test | — | `client/src/__tests__/setup.ts` | role-match |
| `client/src/__tests__/AccountsPage.test.tsx` | test | — | `client/src/__tests__/PrivateRoute.test.tsx` | exact (mock + render + assert) |
| `client/src/__tests__/BalanceEntryForm.test.tsx` | test | — | `client/src/__tests__/PrivateRoute.test.tsx` | exact (mock + render + assert) |
| `client/src/__tests__/HistoryTable.test.tsx` | test | — | `client/src/__tests__/AppSidebar.test.tsx` | exact (render + assert) |
| `client/src/__tests__/LiabilitiesPage.test.tsx` | test | — | `client/src/__tests__/PrivateRoute.test.tsx` | exact (same pattern as AccountsPage test) |
| `client/src/__tests__/PensionPage.test.tsx` | test | — | `client/src/__tests__/PrivateRoute.test.tsx` | exact (same pattern as AccountsPage test) |

---

## Pattern Assignments

### `client/src/lib/queryClient.ts` (utility — QueryClient singleton)

**Analog:** `client/src/lib/firebase.ts` — same singleton module pattern: initialise once, export a named constant, import elsewhere.

**Singleton pattern from `client/src/lib/firebase.ts` (lines 1–8):**
```typescript
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = { ... };
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
```

**Apply this pattern — one module, one export:**
```typescript
// client/src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});
```

**Critical constraint:** The `queryClient` instance is created outside any component tree. Import it into `main.tsx` for the provider and import it into test helpers for `queryClient.invalidateQueries` access.

---

### `client/src/main.tsx` (config — add QueryClientProvider, modify existing)

**Analog:** `client/src/main.tsx` (the file being modified — lines 1–10 show current structure)

**Current file (lines 1–10):**
```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

**Modified pattern — wrap App with QueryClientProvider:**
```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
```

**Constraint:** `QueryClientProvider` wraps `App` — not inside it — so all routes including `/login` have access to the QueryClient. `AuthProvider` and `BrowserRouter` remain inside `App.tsx` unchanged.

---

### `client/src/lib/api/accounts.ts` (service — typed fetch functions)

**Analog:** `client/src/lib/apiClient.ts` — the existing Axios client is the only service-layer analog. All three API modules import `apiClient` and wrap endpoint calls in typed functions.

**Imports pattern from `client/src/lib/apiClient.ts` (lines 1–3):**
```typescript
import axios from 'axios';
import { getIdToken } from 'firebase/auth';
import { auth } from '@/lib/firebase';
```

**API module pattern (all three modules follow this shape):**
```typescript
// client/src/lib/api/accounts.ts
import { apiClient } from '@/lib/apiClient';

// --- TypeScript types (mirror api/schemas/accounts.py field-for-field) ---
export interface AccountTypeResponse {
  id: number;
  name: string;
  is_pension: boolean;
  in_use: boolean;
}

export interface AccountEntryRequest {
  account_type_id: number;
  entry_date: string;   // ISO 'yyyy-MM-dd' — Date serialised by BalanceEntryForm
  balance: number;
  currency?: string;    // defaults to 'GBP' on server
  exchange_rate?: number;
}

export interface EntryItemResponse {
  entry_id: number;
  type_id: number;
  type_name: string;
  balance: number;
}

export interface HistoryDayResponse {
  date: string;
  total: number;
  entries: EntryItemResponse[];
}

// --- Fetch functions used as queryFn / mutationFn ---
export const accountsApi = {
  listTypes: (): Promise<AccountTypeResponse[]> =>
    apiClient.get('/api/accounts/types').then(r => r.data),

  createType: (name: string): Promise<AccountTypeResponse> =>
    apiClient.post('/api/accounts/types', { name }).then(r => r.data),

  updateType: (id: number, name: string): Promise<AccountTypeResponse> =>
    apiClient.put(`/api/accounts/types/${id}`, { name }).then(r => r.data),

  deleteType: (id: number): Promise<void> =>
    apiClient.delete(`/api/accounts/types/${id}`).then(r => r.data),

  createEntry: (body: AccountEntryRequest): Promise<unknown> =>
    apiClient.post('/api/accounts/entries', body).then(r => r.data),

  getHistory: (): Promise<HistoryDayResponse[]> =>
    apiClient.get('/api/accounts/history').then(r => r.data),
};
```

**Type field sources** (from `api/schemas/accounts.py` lines 7–40):
- `AccountTypeResponse`: `id: int, name: str, is_pension: bool, in_use: bool`
- `AccountEntryRequest`: `account_type_id: int, entry_date: date, balance: float, currency: str = "GBP", exchange_rate: float = 1.0`
- `EntryItemResponse`: `entry_id: int, type_id: int, type_name: str, balance: float`
- `HistoryDayResponse`: `date: str, total: float, entries: list[EntryItemResponse]`

---

### `client/src/lib/api/liabilities.ts` (service — typed fetch functions)

**Analog:** Same pattern as `accounts.ts` above. Field names differ per `api/schemas/liabilities.py`.

**Type field sources** (from `api/schemas/liabilities.py` lines 7–38):
- `LiabilityTypeResponse`: `id: int, name: str, in_use: bool` (no `is_pension` field)
- `LiabilityEntryRequest`: field name is `liability_type_id` (not `account_type_id`), `amount: float` (not `balance`)
- `LiabilityHistoryItemResponse`: `entry_id, type_id, type_name, balance` (unified shape per D-01)
- `LiabilityHistoryDayResponse`: same `date, total, entries` shape

**Key differences from accounts.ts:**
- Request body field: `liability_type_id` not `account_type_id`
- Request body field: `amount` not `balance`
- No `exchange_rate` field
- No `is_pension` on type response

---

### `client/src/lib/api/pension.ts` (service — typed fetch functions)

**Analog:** Same pattern as `accounts.ts`. Field names from `api/schemas/pension.py`.

**Type field sources** (from `api/schemas/pension.py` lines 7–39):
- `PensionTypeResponse`: `id: int, name: str, is_pension: bool` (no `in_use` field)
- `PensionEntryRequest`: `account_type_id: int` (same as accounts), `balance: float`, `exchange_rate: float = 1.0`
- `PensionHistoryItemResponse`: same unified `entry_id, type_id, type_name, balance` shape

**Endpoints prefix:** `/api/pension/...` (not `/api/accounts/...`)

---

### `client/src/components/data/DataPage.tsx` (component — generic CRUD+entry+history layout)

**Analog:** `client/src/components/AppLayout.tsx` — same pattern of a layout container that composes child sections via props/children. No direct CRUD analog exists yet.

**AppLayout.tsx layout pattern (lines 1–16):**
```typescript
import { Outlet } from 'react-router-dom';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/AppSidebar';

export function AppLayout() {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-background">
        <AppSidebar />
        <main className="flex-1 p-6 bg-background overflow-auto">
          <Outlet />
        </main>
      </div>
    </SidebarProvider>
  );
}
```

**Apply this section-composition pattern to DataPage:**
```typescript
// client/src/components/data/DataPage.tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { ItemCrudDialog } from './ItemCrudDialog';
import { BalanceEntryForm } from './BalanceEntryForm';
import { HistoryTable } from './HistoryTable';

export interface DataPageConfig<TItem extends { id: number; name: string }> {
  title: string;
  queryKey: readonly string[];
  historyQueryKey: readonly string[];
  fetchItems: () => Promise<TItem[]>;
  fetchHistory: () => Promise<HistoryDayResponse[]>;
  createItem: (name: string) => Promise<unknown>;
  updateItem: (id: number, name: string) => Promise<unknown>;
  deleteItem: (id: number) => Promise<unknown>;
  submitEntry: (body: EntryRequest) => Promise<unknown>;
  itemLabel: string;
}

export function DataPage<TItem extends { id: number; name: string }>({
  config,
}: {
  config: DataPageConfig<TItem>;
}) {
  // useQuery for item list + history
  // useState for dialog open/edit state
  // useMutation for create/update/delete/entry
  // Renders: page header + Add button, ItemCrudDialog, BalanceEntryForm, HistoryTable
}
```

**Import convention:** Named export `export function DataPage` — same as `export function AppLayout`.

**Tailwind class conventions from `AppLayout.tsx` lines 8–12:**
- `flex`, `min-h-screen`, `w-full` for full-page containers
- `p-6` padding for main content area
- `bg-background` for page background

---

### `client/src/components/data/ItemCrudDialog.tsx` (component — add/edit modal)

**Analog:** `client/src/pages/LoginPage.tsx` — best existing example of async form submit with loading state and error display.

**Form + async submit pattern from `LoginPage.tsx` (lines 1–50):**
```typescript
// Imports pattern (lines 1–7):
import { useState } from 'react';
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '@/lib/firebase';
import { useAuth } from '@/contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';

// Loading/error state pattern (lines 9–11):
const [signingIn, setSigningIn] = useState(false);
const [error, setError] = useState(false);

// Async handler with try/catch/finally (lines 16–23):
async function handleSignIn() {
  setSigningIn(true);
  setError(false);
  try {
    await signInWithPopup(auth, googleProvider);
  } catch {
    setError(true);
  } finally {
    setSigningIn(false);
  }
}

// Disabled button during submit (lines 33–37):
<Button
  className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
  disabled={signingIn}
  onClick={handleSignIn}
>
  {signingIn ? 'Signing in...' : 'Sign in with Google'}
</Button>
```

**Apply to ItemCrudDialog — replace useState loading with useMutation.isPending:**
```typescript
// client/src/components/data/ItemCrudDialog.tsx
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import {
  Form, FormField, FormItem, FormLabel, FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
});

interface ItemCrudDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editItem: { id: number; name: string } | null;
  queryKey: readonly string[];
  onCreate: (name: string) => Promise<unknown>;
  onUpdate: (id: number, name: string) => Promise<unknown>;
  itemLabel: string;
}
```

**Dialog controlled-open pattern** (RESEARCH.md Pattern 4): `open` and `onOpenChange` are controlled externally from the parent DataPage. `useEffect` keyed on `[open, editItem?.id]` resets the form to prevent stale values (Pitfall 1 from RESEARCH.md).

**Button disabled pattern** — copy directly from `LoginPage.tsx` line 34–36, replace `signingIn` with `mutation.isPending`:
```typescript
<Button type="submit" disabled={mutation.isPending}>
  {mutation.isPending ? 'Saving...' : 'Save'}
</Button>
```

---

### `client/src/components/data/BalanceEntryForm.tsx` (component — date picker + amount + submit)

**Analog:** `client/src/pages/LoginPage.tsx` — same try/catch/loading-state form submit pattern. No calendar analog exists in the codebase.

**Imports pattern (copy from LoginPage.tsx, extend for RHF + calendar):**
```typescript
// client/src/components/data/BalanceEntryForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Form, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
```

**`cn()` usage — copy from `button.tsx` line 46:**
```typescript
// button.tsx line 46 — cn() for conditional class names
className={cn(buttonVariants({ variant, size, className }))}
// Apply same pattern in BalanceEntryForm for date picker trigger button:
className={cn('w-full justify-start text-left font-normal', !value && 'text-muted-foreground')}
```

**Form submit → mutation pattern** (from LoginPage.tsx async handler, adapted for RHF):
```typescript
const mutation = useMutation({
  mutationFn: (values: EntryValues) =>
    submitEntry({
      ...values,
      entry_date: format(values.entry_date, 'yyyy-MM-dd'),
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: historyQueryKey });
    toast.success('Balance entry saved.');
    form.reset({ entry_date: new Date(), balance: undefined });
  },
  onError: () => toast.error('Failed to save. Please try again.'),
});
```

**Default date to today:** `defaultValues: { entry_date: new Date() }` — mirrors RESEARCH.md Pattern 5.

---

### `client/src/components/data/HistoryTable.tsx` (component — collapsible daily history)

**Analog:** `client/src/components/AppSidebar.tsx` — best existing analog for list-item rendering with conditional class names based on state.

**List render pattern from `AppSidebar.tsx` (lines 29–46):**
```typescript
{navItems.map(({ to, label }) => (
  <SidebarMenuItem key={to}>
    <SidebarMenuButton asChild>
      <NavLink
        to={to}
        end={to === '/'}
        className={({ isActive }) =>
          isActive
            ? 'text-[#58a6ff] font-semibold border-l-2 border-[#58a6ff] py-2 px-4 block transition-colors duration-150'
            : 'py-2 px-4 block transition-colors duration-150 hover:bg-white/5'
        }
      >
        {label}
      </NavLink>
    </SidebarMenuButton>
  </SidebarMenuItem>
))}
```

**Apply to HistoryTable — conditional row class based on `expandedDate` state (not `isActive`):**
```typescript
// client/src/components/data/HistoryTable.tsx
import { useState } from 'react';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import type { HistoryDayResponse } from '@/lib/api/accounts';  // or liabilities/pension

export function HistoryTable({ data }: { data: HistoryDayResponse[] }) {
  const [expandedDate, setExpandedDate] = useState<string | null>(null);
  // ...
}
```

**Conditional row class — copy pattern from AppSidebar.tsx line 37 `isActive` ternary:**
```typescript
className={expandedDate === day.date
  ? 'cursor-pointer bg-muted/50'
  : 'cursor-pointer hover:bg-muted/50'}
```

**Currency formatting:** `Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(value)` — hardcoded GBP per RESEARCH.md Open Question 2.

**React.Fragment key pattern:** Required for collapsible rows (parent row + N child rows share a Fragment key).

---

### `client/src/pages/AccountsPage.tsx` (component — thin config wrapper)

**Analog:** `client/src/pages/AccountsPage.tsx` (existing stub, lines 1–3) — expand it.

**Current stub (lines 1–3):**
```typescript
export function AccountsPage() {
  return <h1 className="text-2xl font-semibold">Accounts</h1>;
}
```

**Replace with config-driven pattern:**
```typescript
// client/src/pages/AccountsPage.tsx
import { DataPage } from '@/components/data/DataPage';
import { accountsApi, type AccountTypeResponse } from '@/lib/api/accounts';
import type { DataPageConfig } from '@/components/data/DataPage';

const config: DataPageConfig<AccountTypeResponse> = {
  title: 'Accounts',
  queryKey: ['accounts', 'types'] as const,
  historyQueryKey: ['accounts', 'history'] as const,
  fetchItems: accountsApi.listTypes,
  fetchHistory: accountsApi.getHistory,
  createItem: accountsApi.createType,
  updateItem: accountsApi.updateType,
  deleteItem: accountsApi.deleteType,
  submitEntry: accountsApi.createEntry,
  itemLabel: 'account',
};

export function AccountsPage() {
  return <DataPage config={config} />;
}
```

**LiabilitiesPage and PensionPage:** Identical structure — substitute `liabilitiesApi` / `pensionApi` and change `title`, query keys, and `itemLabel`.

---

### `client/src/__tests__/test-utils.tsx` (test — renderWithQuery helper)

**Analog:** `client/src/__tests__/setup.ts` — same test infrastructure module, extends the global setup pattern.

**Setup pattern from `setup.ts` (lines 1–10):**
```typescript
// Global test setup — one concern per file, no imports from application code
// @ts-ignore
globalThis.IS_REACT_ACT_ENVIRONMENT = false;
```

**renderWithQuery helper (RESEARCH.md Code Examples):**
```typescript
// client/src/__tests__/test-utils.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import type { RenderResult } from '@testing-library/react';

export function renderWithQuery(ui: React.ReactElement): RenderResult {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}
```

**`retry: false` is critical:** prevents Vitest from timing out on query failures during tests (Pitfall 7 from RESEARCH.md).

---

### `client/src/__tests__/AccountsPage.test.tsx` (test)

**Analog:** `client/src/__tests__/PrivateRoute.test.tsx` — exact pattern: `vi.mock` heavy deps at top, then import component, then describe/it/expect.

**Mock declaration order from `PrivateRoute.test.tsx` (lines 1–17):**
```typescript
import { describe, it, expect, vi } from 'vitest';

// Mocks BEFORE imports — required for vi.mock hoisting
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));
vi.mock('react-router-dom', () => ({
  Navigate: vi.fn(() => null),
  useLocation: vi.fn(() => ({ pathname: '/', search: '', hash: '', state: null, key: 'default' })),
}));

import { render, screen } from '@testing-library/react';
import { PrivateRoute } from '@/components/PrivateRoute';
import { useAuth } from '@/contexts/AuthContext';

const mockUseAuth = vi.mocked(useAuth);
```

**Apply to AccountsPage.test.tsx — mock apiClient and TanStack Query, then test with renderWithQuery:**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

// Mock heavy shadcn components that use Radix portals
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open }: { children: React.ReactNode; open: boolean }) =>
    open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { render, screen } from '@testing-library/react';
import { renderWithQuery } from './test-utils';
import { apiClient } from '@/lib/apiClient';
import MockAdapter from 'axios-mock-adapter';
```

**Mock axios pattern from `apiClient.test.ts` (lines 21–26):**
```typescript
const mockAxios = new MockAdapter(apiClient);

describe('AccountsPage', () => {
  beforeEach(() => {
    mockAxios.reset();
  });
  // ...
});
```

**Assert pattern from `PrivateRoute.test.tsx` lines 39–43:**
```typescript
it('renders children when loading=false and user is authenticated', () => {
  // ...
  expect(screen.getByText('Protected content')).toBeTruthy();
});
```

---

### `client/src/__tests__/HistoryTable.test.tsx` (test)

**Analog:** `client/src/__tests__/AppSidebar.test.tsx` — straightforward render-and-assert test with shadcn component mocks.

**Shadcn mock pattern from `AppSidebar.test.tsx` (lines 13–21):**
```typescript
vi.mock('@/components/ui/sidebar', () => ({
  Sidebar: ({ children }: { children: React.ReactNode }) => <nav>{children}</nav>,
  SidebarContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  // ...each export stubbed to transparent wrapper
}));
```

**Apply to HistoryTable — mock `@/components/ui/table` the same way:**
```typescript
vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: { children: React.ReactNode }) => <table>{children}</table>,
  TableHeader: ({ children }: { children: React.ReactNode }) => <thead>{children}</thead>,
  TableBody: ({ children }: { children: React.ReactNode }) => <tbody>{children}</tbody>,
  TableHead: ({ children }: { children: React.ReactNode }) => <th>{children}</th>,
  TableRow: ({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) =>
    <tr onClick={onClick} className={className}>{children}</tr>,
  TableCell: ({ children, className }: { children: React.ReactNode; className?: string }) =>
    <td className={className}>{children}</td>,
}));
```

**Test renderWithQuery is NOT needed for HistoryTable:** it receives data as props (no useQuery inside). Use plain `render` from testing-library, same as `AppSidebar.test.tsx` line 28.

---

## Shared Patterns

### TanStack Query useMutation + Toast + Invalidation
**Source:** RESEARCH.md Pattern 3 (no codebase analog yet — new pattern for Phase 12)
**Apply to:** `DataPage.tsx`, `ItemCrudDialog.tsx`, `BalanceEntryForm.tsx`

```typescript
// Pattern to copy into every mutation:
const queryClient = useQueryClient();

const mutation = useMutation({
  mutationFn: (payload) => apiFunction(payload),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: relevantQueryKey });
    toast.success('Action completed.');
  },
  onError: () => {
    toast.error('Action failed. Please try again.');
  },
});
```

**Critical:** `queryKey` in `invalidateQueries` must exactly match the `queryKey` in `useQuery` — use the constants defined in page config objects to prevent Pitfall 5 (key mismatch).

### useQuery Pattern for Lists
**Source:** RESEARCH.md Pattern 2 (no codebase analog yet)
**Apply to:** `DataPage.tsx`

```typescript
const { data: items = [], isPending, isError } = useQuery({
  queryKey: config.queryKey,
  queryFn: config.fetchItems,
});
```

**Note:** Use `isPending` not `isLoading` — TanStack Query v5 prefers `isPending` (RESEARCH.md State of the Art).

### Dialog Form Reset (Pitfall Prevention)
**Source:** RESEARCH.md Pattern 4, Pitfall 1
**Apply to:** `ItemCrudDialog.tsx`

```typescript
// CRITICAL: reset on every open with potentially new editItem
useEffect(() => {
  if (open) form.reset({ name: editItem?.name ?? '' });
}, [open, editItem?.id]);
```

**Key on `editItem?.id` not `editItem`** — prevents infinite re-render if `editItem` object reference changes.

### Axios Mock Pattern for Tests
**Source:** `client/src/__tests__/apiClient.test.ts` lines 21–32
**Apply to:** All page test files (`AccountsPage.test.tsx`, `LiabilitiesPage.test.tsx`, `PensionPage.test.tsx`)

```typescript
// From apiClient.test.ts lines 21–32:
const mockAxios = new MockAdapter(apiClient);

describe('...', () => {
  beforeEach(() => {
    mockAxios.reset();
    // reset other mocks
  });
  afterEach(() => {
    vi.clearAllMocks();
  });
});
```

### Shadcn Component Stubbing for Tests
**Source:** `client/src/__tests__/AppSidebar.test.tsx` lines 13–21
**Apply to:** All test files that render Dialog, Calendar, Popover, Form, or Table

The established project pattern: every shadcn Radix-backed component is stubbed with a transparent wrapper in the test. **Mock heavy components before importing the component under test** (vi.mock hoisting requirement from `PrivateRoute.test.tsx` lines 5–16).

```typescript
// Pattern: stub each named export as a transparent wrapper
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open }) => open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children }) => <div>{children}</div>,
  DialogHeader: ({ children }) => <div>{children}</div>,
  DialogTitle: ({ children }) => <div>{children}</div>,
  DialogFooter: ({ children }) => <div>{children}</div>,
}));
```

### Named Export Convention
**Source:** All existing `client/src/` files
**Apply to:** All Phase 12 components and pages

Every component uses `export function Foo()` (named export) — NOT `export default`. Confirmed in:
- `client/src/components/AppLayout.tsx` line 5: `export function AppLayout()`
- `client/src/components/AppSidebar.tsx` line 22: `export function AppSidebar()`
- `client/src/components/PrivateRoute.tsx` line 4: `export function PrivateRoute()`
- `client/src/pages/LoginPage.tsx` line 8: `export function LoginPage()`

Exception: `App.tsx` line 13 uses `export default function App()` (Vite entry point convention — do not change).

### `cn()` Utility Import
**Source:** `client/src/lib/utils.ts` line 4, used in `button.tsx` line 6
**Apply to:** `BalanceEntryForm.tsx` (date picker trigger button conditional class)

```typescript
import { cn } from '@/lib/utils';
// Usage: cn('base-classes', conditionalBool && 'conditional-class')
```

### Toast via sonner (NOT useToast)
**Source:** RESEARCH.md Project Constraints — locked Phase 11 decision; `sonner` confirmed in project but not yet in `package.json` (must be installed in Wave 0 alongside shadcn components)
**Apply to:** `ItemCrudDialog.tsx`, `BalanceEntryForm.tsx`, `DataPage.tsx` (delete confirmation)

```typescript
import { toast } from 'sonner';
// Usage:
toast.success('Message here.');
toast.error('Error message here.');
```

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `client/src/lib/queryClient.ts` | utility | — | Closest is firebase.ts (singleton pattern) but TanStack Query setup is net-new; use RESEARCH.md Pattern 1 |
| shadcn `dialog.tsx`, `form.tsx`, `calendar.tsx`, `popover.tsx`, `table.tsx`, `label.tsx`, `select.tsx` | ui | — | Auto-generated by `npx shadcn@2.3.0 add` — no analog, no manual authoring |

---

## Metadata

**Analog search scope:** `client/src/` (all subdirs), `api/schemas/` (for TypeScript type shapes), `api/routers/accounts.py` (for API contract)
**Files scanned:** 22 (`apiClient.ts`, `main.tsx`, `App.tsx`, `AppLayout.tsx`, `AppSidebar.tsx`, `PrivateRoute.tsx`, `AuthContext.tsx`, `LoginPage.tsx`, `AccountsPage.tsx` stub, `LiabilitiesPage.tsx` stub, `PensionPage.tsx` stub, `utils.ts`, `button.tsx`, `input.tsx`, `setup.ts`, `AppSidebar.test.tsx`, `PrivateRoute.test.tsx`, `apiClient.test.ts`, `firebase-auth.ts` mock, `firebase-app.ts` mock, `vitest.config.ts`, `package.json`, plus 3 schema files and accounts router)
**Pattern extraction date:** 2026-05-14
