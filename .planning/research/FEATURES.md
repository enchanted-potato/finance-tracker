# Feature Research

**Domain:** React + TypeScript SPA — Personal Net Worth Tracker (v2.0 React Migration)
**Researched:** 2026-04-04
**Confidence:** HIGH — Based on direct codebase analysis of all six Streamlit pages plus training knowledge of shadcn/ui (component set stable through late 2024) and React SPA UX patterns. Web fetch unavailable; shadcn/ui knowledge flagged where version-sensitive.

---

## Context

This is a page-for-page rebuild of an existing working Streamlit app into React + TypeScript + shadcn/ui. All business logic is preserved; only the frontend changes. The question being answered is: **how does each feature work in a React SPA context, what UX patterns apply, and which shadcn/ui components map to each page?**

The app is single-user and personal. That drives every recommendation: no multi-tenancy, no collaborative editing, no real-time sync needed. Optimistic updates are desirable for snappiness but not required for shared-state correctness.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features assumed by anyone using a web app in 2025. Missing these makes the app feel broken compared to the Streamlit version.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Persistent auth state across page reloads | Firebase JS SDK with `browserLocalStorage` persistence — losing auth on refresh is a regression | LOW | `onAuthStateChanged` listener on app mount; show loading skeleton until auth state resolves. Never flash unauthenticated state |
| Loading skeletons on data fetch | SPA fetches are async — blank pages feel broken | LOW | `Skeleton` component from shadcn/ui on every data-bearing section. Show immediately; replace on data arrival |
| Error boundary + user-visible fetch errors | Network errors, 401s, 500s must not silently fail | LOW | React Error Boundary at router level; `toast` (Sonner) for per-operation errors |
| Client-side navigation without full reload | SPA expectation — page transitions should be instant | LOW | React Router v6 `<Link>` / `useNavigate()`. No full page loads after initial bundle |
| Responsive layout (desktop-first, usable on tablet) | Web app standard | MEDIUM | Tailwind responsive prefixes. Dashboard grid collapses at `md:` breakpoint. Tables scroll horizontally on small screens |
| Form validation with inline errors | React Hook Form + Zod pattern is standard | LOW | Never show errors on empty form. Show inline under field after first submit attempt or on blur |
| Currency formatting | Financial app must format numbers consistently (£1,234.56) | LOW | `Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' })`. Centralise in a `formatCurrency()` utility |
| Empty state messaging | Every list/table must handle the zero-data state gracefully | LOW | Inline `<p>` with instructional text (matches Streamlit `st.info()` pattern). Not a dedicated component |
| Keyboard navigation and focus management | Dialogs must trap focus; forms must be tabable | MEDIUM | shadcn/ui `Dialog` uses Radix UI primitives which handle focus trapping automatically |

### Differentiators (React SPA vs Streamlit Baseline)

Features the React version can do better than Streamlit, or features specific to this app that need careful handling.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Optimistic UI on balance save | Accounts/Liabilities/Pension saves feel instant rather than waiting for the API round-trip | MEDIUM | React Query `useMutation` with `onMutate` optimistic update + `onError` rollback. Worth doing because saves are frequent. Single-user means no conflict risk |
| Expandable row detail in History | Inline breakdown of accounts + liabilities per snapshot — the Streamlit version re-renders the whole page on toggle | LOW | Local `useState` per row for open/closed. No server call needed — detail is in the row's `detail_json` from the initial fetch |
| Inline delete with confirmation | Configure page deletes types — React can show a `AlertDialog` without re-fetching the whole page | LOW | shadcn/ui `AlertDialog` with destructive variant. Only fetch after confirmed delete |
| Chart interactivity | Recharts tooltips, legend toggles — more responsive than Plotly in Streamlit's iframe model | MEDIUM | Recharts `<Tooltip>` + `<Legend>` with payload toggling. Time range filter updates chart data locally (no refetch) |
| Date-aware balance entry UX | Accounts page lets users enter balances for any past date — the date picker matters | MEDIUM | shadcn/ui `Calendar` inside a `Popover` (the "DatePicker" pattern). Default to today; allow past dates freely |
| Toast feedback on mutations | Success/error feedback that doesn't block the UI (replacing Streamlit's `st.success()` banner) | LOW | Sonner `toast.success()` / `toast.error()` triggered from React Query mutation callbacks |
| Sticky sidebar navigation | Sidebar stays fixed during scroll — Streamlit's sidebar has visual jitter on rerun | LOW | CSS `position: sticky` or fixed sidebar with `overflow-y: auto` on content area |

### Anti-Features (Avoid These)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time data sync / WebSocket | "Always up to date" sounds good | Single user, manual balance entry — there's nothing to sync in real time. WebSockets add auth complexity and Cloud Run connection limits | `useQuery` with `staleTime: 5 * 60 * 1000`. Data is fresh enough |
| Client-side optimistic updates for snapshot creation | Snapshots are auto-created on the server after balance saves | The server computes net worth from all current balances; the client can't replicate that calculation | Show a loading state after save; invalidate and refetch snapshot queries |
| Inline table editing (spreadsheet-style) | Streamlit uses `st.data_editor` for this | Implementing a full spreadsheet editor in React is weeks of work. The Streamlit pattern works because Streamlit owns the grid component | Replace with row-level edit dialogs or a dedicated "Add entry" form. Much simpler, standard React pattern |
| Pagination on history table | "Best practice for large datasets" | This user has at most ~36-48 rows (3-4 years of monthly snapshots). Pagination adds UI complexity with zero benefit | Render all rows. Add year-group dividers for visual structure (as Streamlit does) |
| Dark mode toggle | Users expect it | The app is dark-only ("Midnight" scheme). Adding a toggle means designing and maintaining two themes | Hard-code dark mode via Tailwind `darkMode: 'class'` with `dark` class on `<html>`. No toggle |
| CSV upload via drag-and-drop | Modern file upload UX | shadcn/ui doesn't include a drop-zone component; adding a third-party one for a feature used once during data migration adds bundle size | Plain `<input type="file" accept=".csv">` styled to match. Used so rarely, UX polish isn't worth it |

---

## shadcn/ui Component Mapping Per Page

This is the primary deliverable for the roadmap. Each page's component requirements, with rationale.

### All Pages — Shared Components

| Component | Use | Notes |
|-----------|-----|-------|
| `Sidebar` / `SidebarProvider` | Navigation shell — links to Dashboard, Accounts, Liabilities, Pension, History, Configure | shadcn/ui has a `Sidebar` component suite (added ~mid-2024). Use it over rolling custom sidebar |
| `Skeleton` | Loading state for any data-fetching section | Use matching shapes (card-shaped for metric cards, row-shaped for tables) |
| `Sonner` (Toast) | Success/error feedback for mutations | Use `toast.success()` for saves, `toast.error()` for API errors. Import from `sonner` package; shadcn/ui wraps it |
| `Button` | Every CTA | Variants: `default`, `destructive`, `outline`, `ghost`. Use `destructive` for delete actions |

### Dashboard Page

The dashboard is read-only — no mutations, just data display.

| Component | Use | Notes |
|-----------|-----|-------|
| `Card`, `CardHeader`, `CardContent` | Four metric cards: Net Worth, Total Assets, Total Liabilities, Total Pension | `CardContent` holds the big number; `CardHeader` holds the label. Add a delta badge inside `CardContent` for the net worth change |
| `Badge` | Net worth delta (e.g., "+£1,234" in green / "−£500" in red) | Use `variant="outline"` and override colour with Tailwind. Avoid shadcn's semantic variants (success/destructive) since they aren't available by default |
| `ToggleGroup` (or `Tabs`) | Time range filter: 6 Months / 1 Year / All Time | `ToggleGroup` with `type="single"` is the correct semantic fit — one option selected at a time, not separate pages. Sits above the trend chart |
| `Recharts` (not shadcn/ui) | Line chart (net worth trend), donut charts (asset/liability allocation), stacked bar (pension) | Recharts maps well: `<LineChart>` for trend, `<PieChart hole>` for donuts, `<BarChart barSize>` for pension. Wrap each in a `Card` |
| `Separator` | Visual divider between chart sections | `<Separator>` component or plain `<hr>` with Tailwind |

### Accounts Page (and Liabilities Page, Pension Page — same pattern)

These three pages are identical in structure. They manage date-keyed balance entries with a running total card.

| Component | Use | Notes |
|-----------|-----|-------|
| `Card` | Summary metric card (e.g., "Total Assets — £45,000") | Same pattern as Dashboard metric cards. Single card, takes 1/4 width on desktop |
| `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` | Balance history table — one row per entry (Date, Type, Balance, Currency, Rate, actions) | shadcn/ui `Table` wraps HTML table elements. Use `TableCell` with `font-mono` class for numeric columns |
| `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogFooter` | "Add / Edit entry" form — opened via "Add entry" button or row-level edit action | Replace Streamlit's inline data editor with a dialog form. Simpler, more standard React UX |
| `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormMessage` | Inside the Dialog — React Hook Form + shadcn/ui form primitives | Required for validation errors per field |
| `Input` | Balance field, currency field, exchange rate field | `type="number"` for Balance and Rate; `type="text"` for Currency (3-char uppercase) |
| `Select`, `SelectContent`, `SelectItem` | Account/liability type dropdown | Types fetched from API. Show type name; send type ID to API |
| `Popover` + `Calendar` | Date picker for entry date | The shadcn/ui DatePicker pattern: a `Button` that opens a `Popover` containing a `Calendar`. Default to today; allow past dates |
| `AlertDialog` | Delete row confirmation | "Delete this entry?" with Cancel / Delete (destructive) buttons. Fire API call only after confirmation |
| `Button` (ghost, small) | Edit and Delete triggers per table row | Icon buttons in the actions column. Use `Pencil` and `Trash2` from `lucide-react` |

**Key UX decisions for these pages:**

- **Replace inline data editor with row-level dialogs.** Streamlit's `st.data_editor` (spreadsheet grid) has no equivalent in React without a third-party grid library. The correct React pattern is a table with per-row action buttons that open a dialog. This is simpler to build and more standard.
- **Add "New Entry" button above the table.** Opens the same Dialog as the edit action, but pre-filled with today's date.
- **Optimistic add/edit/delete.** React Query mutations: on mutate, update the local cache; on error, roll back and show toast. The table re-renders instantly.
- **Sort table newest-first by default.** Match the Streamlit ordering. No user-facing sort controls needed.

### History Page

The most visually custom page — custom row rendering with year dividers and expandable detail panels.

| Component | Use | Notes |
|-----------|-----|-------|
| `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` | Snapshot history table — Month, Assets, Liabilities, Net Worth, Change, Actions | Use monospace font class on all number cells. `TableCell` with `colSpan` for the expandable detail panel row |
| `Badge` | Change column — "+£1,234" positive/negative colours | Same approach as Dashboard delta badge |
| `Collapsible` (Radix primitive, exported by shadcn/ui) | Expandable detail row — per-snapshot account breakdown | `CollapsibleTrigger` on the expand button, `CollapsibleContent` renders the detail panel below the main row. Lives inside a `<tr>` spanning all columns |
| `Dialog`, `DialogContent`, etc. | Edit snapshot modal — assets, liabilities fields | Same Dialog pattern as Accounts. Fields: Total Assets (number), Total Liabilities (number or null) |
| `Separator` | Year dividers between groups of monthly rows | A `<Separator>` with the year label overlaid using absolute positioning, or a dedicated `<tr>` spanning all columns |
| `Button` | "Download CSV" and "Upload CSV" | Standard `Button` for download (triggers `window.URL.createObjectURL()`). File input styled as a `Button` for upload |
| `Input` (`type="file"`) | CSV upload — snapshots import and liabilities import | Hide native input; trigger via `Button`. Two separate upload areas (Snapshots CSV, Liabilities CSV) |

**Key UX decisions:**

- **Group rows by year with a divider row.** Render `<tr>` with `colSpan={6}` as year headers. Simpler than the Streamlit custom HTML approach.
- **Expandable row detail uses `Collapsible` component.** When open, renders an additional `<tr>` below with a two-column grid of accounts and liabilities from `detail_json`. This replaces the Streamlit toggle button + session state pattern.
- **Edit modal is identical to the Streamlit `@st.dialog("Edit Snapshot")` pattern** — just Total Assets + Total Liabilities fields.
- **CSV export triggers a download.** Build the CSV in the browser from the fetched data (no round-trip to server needed). Use `Blob` + `URL.createObjectURL()`. Avoids a dedicated export endpoint.

### Configure Page

Type management — CRUD for account types and liability types.

| Component | Use | Notes |
|-----------|-----|-------|
| `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` | "Account Types" / "Liability Types" tab switch | Direct equivalent of Streamlit's `st.tabs()` |
| `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` | List of existing types — columns: Name, Pension (checkbox), Usage count, Actions | Keep table minimal — this is a settings screen, not a data screen |
| `Checkbox` | "Is pension" flag per account type row | Controlled checkbox; fires PATCH immediately on change (no "Save" button needed). Show loading state on the checkbox while the request is in flight |
| `Input` + `Button` | "Add new type" inline form at top of each tab | `Input` for the name, `Button` to submit. No Dialog needed — the form is always visible, compact |
| `AlertDialog` | Confirm before deleting an unused type | "Delete 'Savings Account'?" with Cancel / Delete (destructive). Only show the delete button when usage count is 0 |
| `Badge` | Usage count per type — e.g., "3 accounts" | `variant="secondary"` badge in the Usage column |
| `Button` (ghost, icon-only) | Delete button per deletable row | `Trash2` icon from lucide-react. Disabled (greyed) when usage > 0. Tooltip explaining why |

**Key UX decisions:**

- **"Pension" toggle fires immediately** (no save button). This is the natural UX for a checkbox in a settings table — user toggles, app saves. Show a loading spinner on the row briefly.
- **Inline add form always visible** (not in a dialog). The form is simple (one text field). Always showing it reduces friction for a settings screen.
- **Delete is per-row, gated on usage = 0.** Disabled button when in use, with `Tooltip` explaining "Cannot delete — in use by N entries."
- **Rename via `Input` in the table row.** User clicks the name, it becomes editable inline. On blur or Enter, fire PATCH. More discoverable than a dialog for renaming.

### Auth Page (Login Screen)

Not a Streamlit page — new in the React version.

| Component | Use | Notes |
|-----------|-----|-------|
| `Card`, `CardHeader`, `CardContent`, `CardFooter` | Login form container — centred on screen | Use CSS `min-h-screen flex items-center justify-center` to center |
| `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormMessage` | Email + password fields with validation | Zod schema: email format + non-empty password |
| `Input` | Email (type="email"), Password (type="password") | Show password toggle button inside the input |
| `Button` | "Sign in with Google" (primary), "Sign in with email" (secondary) | Google button: `outline` variant with Google logo SVG. Email/password submit: `default` variant |
| `Alert`, `AlertDescription` | Auth error display (wrong password, network error) | Show below the form after failed attempt. Use `variant="destructive"` |

---

## UX Patterns That Apply — Single-User Context

### Loading States

**Pattern:** Always show skeleton first, never a blank page.

Every page fetches data on mount. The sequence is:
1. Component mounts → show `Skeleton` placeholders matching the shape of the final content.
2. React Query returns data → replace skeletons with real content.
3. Never flash "No data" before data has actually loaded.

Implementation: `isLoading` from `useQuery` drives skeleton rendering. `isError` drives error state. Both are checked before rendering content.

### Error Handling

**Pattern:** Toast for recoverable errors, Error Boundary for unrecoverable ones.

- API mutation fails (save balance, delete type) → `toast.error("Failed to save. Please try again.")`. No navigation.
- API read fails (page data) → inline `Alert` with retry button.
- Unhandled throw → React Error Boundary renders a fallback with a "Reload page" button.

**Single-user note:** No conflict detection needed. There's one writer (the user). Retry is always safe.

### Optimistic Updates

**Pattern:** Use optimistic updates for mutations on the three balance-entry pages (Accounts, Liabilities, Pension) and Configure.

React Query `useMutation`:
```
onMutate: update local cache immediately
onError: roll back cache to previous state, show toast
onSettled: invalidate queries to re-sync with server
```

**Do not use optimistic updates for snapshot data.** Snapshots are server-computed (sum of all current balances). The client can't replicate the calculation. After a balance save, invalidate snapshot queries and let them refetch.

### Form Validation

**Pattern:** React Hook Form + Zod. Validate on submit first time; switch to validate-on-change after first submit.

Validation rules per form type:
- **Balance entry:** date required, type required (select), balance >= 0 (number), currency 3 chars uppercase, rate > 0.
- **Type name:** non-empty string, max 100 chars, trimmed.
- **Snapshot edit:** total assets >= 0, total liabilities >= 0 or null.

Show errors inline under each field using `FormMessage`. Never disable the submit button based on validity (disabling buttons before the user has had a chance to see errors is poor UX).

### Mutation Feedback

**Pattern:** Button loading state during in-flight request + toast on completion.

```
User clicks "Save" →
  Button shows spinner (disabled)
  Optimistic update applied to table
  API call fires
  On success: button returns to normal, toast.success("Saved")
  On error: rollback, button returns to normal, toast.error(message)
```

### Date Picker

**Pattern:** shadcn/ui DatePicker (Popover + Calendar).

Default value: today's date for new entries.
Constraint: allow any past date freely. No minimum date restriction.
Format displayed in button: "Mar 2025" (month/year format to match the app's snapshot granularity convention). Show full date (15 Mar 2025) for the entry form; the month label is derived on the server.

---

## Feature Dependencies

```
[Firebase Auth (onAuthStateChanged)]
    └──must resolve──> [any page renders]

[Account Types API]
    └──required by──> [Accounts page — type dropdown]
    └──required by──> [Pension page — pension type dropdown]
    └──required by──> [Configure page — account types tab]

[Liability Types API]
    └──required by──> [Liabilities page — type dropdown]
    └──required by──> [Configure page — liability types tab]

[Balance Entries API (accounts, liabilities, pension)]
    └──required by──> [Dashboard — metric cards and chart data]
    └──required by──> [History — snapshot context]

[Snapshot API]
    └──depends on──> [balance saves triggering server-side snapshot capture]
    └──displayed on──> [Dashboard trend chart]
    └──displayed on──> [History table]

[shadcn/ui Dialog (Accounts/Liabilities/Pension)]
    └──requires──> [Account/Liability Types loaded] (to populate Select options)

[CSV Export (History)]
    └──can be built from client-side data] (no server endpoint needed)

[CSV Import (History)]
    └──requires──> [dedicated FastAPI endpoint] (server parses CSV, writes snapshots)
```

### Dependency Notes

- **Auth must resolve before any page data fetches.** Firebase `onAuthStateChanged` is async. Render a full-page loading state until auth state is known. Only then mount route-protected pages that trigger API calls with the auth token.
- **Type lists must be fetched before entry forms open.** The Add/Edit entry dialog's type `Select` is populated from the types API. If types aren't loaded, the dialog shouldn't open. Use React Query with `enabled: !!accountTypes` on dependent queries, or pre-fetch types at the page level before rendering the "Add" button.
- **Dashboard reads the same data as account/liability pages.** Keep these in separate React Query keys so mutations on the Accounts page correctly invalidate the Dashboard's data.

---

## MVP Definition

This milestone is a 1:1 rebuild, not a feature expansion. MVP = all existing Streamlit features working in React.

### Must Ship (v2.0 Launch)

- [ ] Firebase Google Sign-In — single-click auth (replaces email/password as primary since user is the developer)
- [ ] Dashboard: 4 metric cards, time-range toggle, line chart, 2 donut charts, pension bar chart
- [ ] Accounts page: balance history table, add/edit/delete entry dialog, date picker, type select
- [ ] Liabilities page: same pattern as Accounts
- [ ] Pension page: same pattern as Accounts (simplified — no currency/exchange rate)
- [ ] History page: monthly snapshot table with year dividers, expandable detail rows, edit modal, delete
- [ ] History page: CSV export (client-side) and CSV import (two upload areas)
- [ ] Configure page: account types and liability types CRUD with pension flag toggle and inline delete
- [ ] Midnight dark colour scheme applied globally
- [ ] Sidebar navigation between all pages
- [ ] Loading skeletons on all data-bearing sections
- [ ] Toast feedback for all mutations

### Add After v2.0 (if desired)

- [ ] Time range filter persisted in URL (e.g., `?range=6m`) — allows bookmarking a specific view
- [ ] Keyboard shortcut to open "Add entry" dialog (e.g., `n` key) — power user convenience
- [ ] Chart data labels on hover showing exact values — minor Recharts enhancement

### Explicitly Out of Scope

- [ ] Transaction tracking — not part of the product
- [ ] Multi-currency conversion — out of scope per PROJECT.md
- [ ] Real-time sync — unnecessary

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Firebase Auth + auth gate | HIGH | LOW | P1 |
| Sidebar navigation | HIGH | LOW | P1 |
| Dashboard metric cards | HIGH | LOW | P1 |
| Dashboard trend line chart | HIGH | MEDIUM | P1 |
| Dashboard donut charts | HIGH | MEDIUM | P1 |
| Accounts balance table + CRUD dialog | HIGH | MEDIUM | P1 |
| Liabilities balance table + CRUD dialog | HIGH | MEDIUM | P1 |
| Pension balance table + CRUD dialog | HIGH | LOW | P1 (simpler than accounts) |
| History snapshot table + year dividers | HIGH | MEDIUM | P1 |
| History expandable detail rows | MEDIUM | LOW | P1 |
| History edit/delete snapshot | MEDIUM | LOW | P1 |
| History CSV export (client-side) | MEDIUM | LOW | P1 |
| History CSV import | MEDIUM | MEDIUM | P1 |
| Configure type CRUD | HIGH | LOW | P1 |
| Configure pension flag toggle | MEDIUM | LOW | P1 |
| Loading skeletons | MEDIUM | LOW | P1 |
| Toast mutation feedback | MEDIUM | LOW | P1 |
| Optimistic updates (balance pages) | LOW | MEDIUM | P2 |
| Dashboard pension bar chart | LOW | LOW | P2 (only shown if pension data exists) |
| URL-persisted time range filter | LOW | LOW | P3 |

---

## Sources

- Direct codebase analysis — all six Streamlit page files read in full: `dashboard.py`, `accounts.py`, `liabilities.py` (same pattern), `pension.py`, `history.py`, `configure.py` — HIGH confidence
- `.planning/PROJECT.md` — milestone requirements and constraints — HIGH confidence
- `shadcn/ui` component inventory: training knowledge through August 2025. Components referenced (`Card`, `Table`, `Dialog`, `Form`, `Input`, `Select`, `Popover`, `Calendar`, `AlertDialog`, `Tabs`, `Badge`, `Skeleton`, `Sidebar`, `Collapsible`, `Checkbox`, `Tooltip`, `Alert`, `Separator`, `ToggleGroup`, `Button`) are all stable components present since shadcn/ui's stable period (mid-2023 onward) — MEDIUM confidence (verify `Sidebar` component API specifically, as it was added later and may have evolved)
- React Query v5 optimistic update pattern (`onMutate` / `onError` / `onSettled`) — MEDIUM confidence (pattern is stable; verify `useMutation` API shape against current TanStack Query v5 docs at implementation)
- React Hook Form + Zod integration pattern — HIGH confidence (extremely stable, unchanged API)
- Sonner toast library (used by shadcn/ui as the recommended toast solution) — MEDIUM confidence (verify `sonner` is the current shadcn/ui recommendation vs older `useToast` hook)

---

*Feature research for: React + TypeScript SPA rebuild of personal net worth tracker*
*Researched: 2026-04-04*
