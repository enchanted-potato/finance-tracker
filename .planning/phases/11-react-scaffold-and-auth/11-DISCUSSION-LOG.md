# Phase 11: React Scaffold and Auth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 11-react-scaffold-and-auth
**Areas discussed:** App directory, Midnight theme, Page shells, Dev setup

---

## App directory

| Option | Description | Selected |
|--------|-------------|----------|
| react/ | Purpose-named, unambiguous | |
| web/ | Tech-agnostic, shorter | |
| client/ | Conventional for full-stack repos; pairs with api/ and app/ | ✓ |

**User's choice:** `client/`
**Notes:** Mirrors the existing `api/` and `app/` top-level directories.

---

## Midnight theme

### Question 1: Fidelity level

| Option | Description | Selected |
|--------|-------------|----------|
| Pixel-perfect port | Map all hex values (#161b22, #e6edf3, #8b949e, #30363d, #58a6ff) to shadcn/ui CSS variables | |
| shadcn/ui dark preset + tweaks | Start with built-in dark theme, adjust background and accent | ✓ |
| You decide | Claude picks approach | |

**User's choice:** shadcn/ui dark preset + tweaks

### Question 2: Which colours to lock

| Option | Description | Selected |
|--------|-------------|----------|
| Background + accent only | Lock --background (#161b22) and --primary (#58a6ff); rest uses shadcn defaults | ✓ |
| All surface colours | Background, text, muted, border, card all match Streamlit palette | |
| You decide | Claude picks which variables to override | |

**User's choice:** Background + accent only

### Question 3: Poppins font

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, Poppins via Google Fonts | @import in index.css; font-sans set in tailwind.config | ✓ |
| No, shadcn/ui default (Inter) | Simpler, no external font dependency | |

**User's choice:** Yes, Poppins globally

---

## Page shells

### Question 1: Which pages to stub

| Option | Description | Selected |
|--------|-------------|----------|
| All 6 page stubs | Dashboard, Accounts, Liabilities, Pension, History, Configure — all routes resolve | ✓ |
| Dashboard stub only | Other routes added as each phase ships | |
| You decide | Claude picks the page set | |

**User's choice:** All 6 stubs

### Question 2: Sidebar order

| Option | Description | Selected |
|--------|-------------|----------|
| Dashboard, Accounts, Liabilities, Pension, History, Configure | Matches existing Streamlit sidebar order | ✓ |
| You decide | Claude picks the order | |

**User's choice:** Matches existing Streamlit order

---

## Dev setup

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone npm run dev | cd client && npm run dev; no docker-compose changes | ✓ |
| Add to docker-compose | Consistent with Phase 9 FastAPI wiring | |

**User's choice:** Standalone — defer docker-compose to Phase 15

---

## Claude's Discretion

- Internal file layout within `client/src/` (pages/, components/, lib/, hooks/)
- shadcn/ui init flags and style variant
- React Router v6 setup and route definitions
- Firebase SDK initialization location
- Auth state management approach (React Context)
- Sidebar component choice
- Loading spinner while `onAuthStateChanged` resolves

## Deferred Ideas

- docker-compose integration for the React dev server — deferred to Phase 15
