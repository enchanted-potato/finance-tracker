# Phase 10: Core Data API Routes - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

All feature endpoints (accounts, liabilities, pension, snapshots, configure) are live and returning correctly shaped data. Route handlers are thin — all business logic stays in `app/services/`. The API contract is the single source of truth for data shaping before any React work begins.

</domain>

<decisions>
## Implementation Decisions

### Entry history shape
- **D-01:** `GET /api/accounts/history`, `GET /api/liabilities/history`, `GET /api/pension/history` return an array grouped by date:
  ```json
  [
    {
      "date": "2025-01-15",
      "total": 25000.50,
      "entries": [
        {"entry_id": 1, "type_id": 3, "type_name": "ISA", "balance": 15000.00},
        {"entry_id": 2, "type_id": 5, "type_name": "Current", "balance": 10000.50}
      ]
    }
  ]
  ```
- **D-02:** `entry_id` is included in each entry so React delete/edit actions target the correct record directly.
- **D-03:** `total` is computed server-side (not by the client). Newest dates first.

### Auto-snapshot on balance write
- **D-04:** Every POST or PUT to a balance entry endpoint (accounts, liabilities, pension) automatically calls `capture_snapshot()` for the entry's date before returning. No separate snapshot endpoint needed — mirrors Streamlit behavior exactly. Transparent to the React client.

### Monetary values in JSON
- **D-05:** All monetary values returned as JSON numbers (floats), not strings. `{"balance": 1250.50}`. Recharts and JS math work natively. Personal finance values are well within float precision range.
- **D-06:** Pydantic schemas use `float` (not `Decimal`) for response models. Request bodies accept `float` — Pydantic coerces from string if needed.

### Dashboard endpoint
- **D-07:** Include `GET /api/dashboard` in Phase 10 — API contract is complete before any React work. Returns Recharts-shaped data for trend chart, asset allocation, and pension chart. Phase 13 is pure React with no API work.
- **D-08:** Recharts format for trend: one object per date with all series as keys, e.g. `[{"date": "2025-01-15", "net_worth": 24000.50, "assets": 25000.50, "liabilities": 1000.00}]`.
- **D-09:** Allocation data: one slice per asset type `[{"name": "ISA", "value": 15000.00}]`.
- **D-10:** Pension data: one bar per provider `[{"name": "SIPP", "value": 45000.00}]`.

### Account/liability type endpoints
- **D-11:** `GET /api/account-types` and `GET /api/liability-types` include `in_use: bool` per type (using existing `account_type_usage_count()` / `liability_type_usage_count()` from `type_service.py`). The in-use check is done server-side — React uses it to disable delete buttons.
- **D-12:** DELETE on a type that is in use returns HTTP 409 Conflict, not 422. The existing `ValueError` from `delete_account_type()` is mapped to 409.

### Pension endpoint structure
- **D-13:** Pension is a filtered view of accounts (`is_pension=True`). Separate routes under `/api/pension/` mirror accounts exactly: `GET /api/pension/types`, `GET /api/pension/entries`, `POST /api/pension/entries`, `DELETE /api/pension/entries/{id}`, `GET /api/pension/history`. Internally calls the same service functions with pension filtering.

### Snapshot endpoints
- **D-14:** `GET /api/snapshots/export.csv` returns a `StreamingResponse` with `Content-Disposition: attachment; filename=snapshots.csv`.
- **D-15:** `POST /api/snapshots/import` accepts multipart `UploadFile`. Returns `{imported, skipped, errors}` — already the return type of `import_csv_snapshots()`.
- **D-16:** `GET /api/snapshots` returns the history list for display in Phase 14's History page (ordered ascending by date).

### Claude's Discretion
- Exact URL path naming (e.g. `/entries` vs `/balance-entries`)
- Schema field ordering and optional fields on request bodies
- Router file structure under `api/routers/`
- How to handle `DELETE /api/snapshots/{id}` (already exists in `snapshot_service.delete_snapshot()`)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing services (all routes must wrap these — do not duplicate logic)
- `app/services/account_service.py` — CRUD + entry functions for accounts and pension
- `app/services/liability_service.py` — CRUD + entry functions for liabilities
- `app/services/snapshot_service.py` — `capture_snapshot()`, `get_snapshot_history()`, CSV import/export
- `app/services/type_service.py` — Account/liability type CRUD with in-use checks

### Existing API foundation (Phase 9 output)
- `api/main.py` — App factory, CORS config, lifespan (Firebase Admin init)
- `api/dependencies.py` — `get_current_user` dependency, dev bypass pattern
- `api/routers/health.py` — Example of how routers are structured
- `api/schemas/health.py` — Example of how schemas are structured

### Models
- `app/models.py` — `AccountEntry`, `AccountType`, `LiabilityEntry`, `LiabilityType`, `Snapshot`

### Phase requirements
- `.planning/REQUIREMENTS.md` §API-05, API-06, API-07, API-08

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/services/account_service.py` — `list_account_types()`, `list_account_entries()`, `list_non_pension_entries()`, `list_pension_entries()`, `upsert_account_entry()`, `delete_account_entry()`
- `app/services/liability_service.py` — `list_liability_types()`, `list_liability_entries()`, `upsert_liability_entry()`, `delete_liability_entry()`
- `app/services/snapshot_service.py` — `capture_snapshot()` (auto-call after every balance write), `get_snapshot_history()`, `get_latest_snapshot()`, `import_csv_snapshots()`, `delete_snapshot()`
- `app/services/type_service.py` — `create_account_type()`, `delete_account_type()`, `account_type_usage_count()`, `create_liability_type()`, `delete_liability_type()`, `liability_type_usage_count()`
- `api/dependencies.py` — `get_current_user` is the established auth pattern

### Established Patterns
- Route handlers are thin: call service, return schema — no business logic in routes
- All service functions are keyword-only (`session=`, `user_id=`)
- `Depends(get_session)` from `app/database.py` directly (no wrapper)
- `Depends(get_current_user)` from `api/dependencies.py` for all non-health endpoints
- Schema files in `api/schemas/` — flat, one file per domain
- Router files in `api/routers/` — one per domain (health.py is the example)

### Integration Points
- `api/main.py`: New routers added via `app.include_router()`
- `app/database.py`: `get_session()` is the session provider — unchanged
- Pension is not a separate table — it is `AccountEntry` filtered by `AccountType.is_pension=True`; `account_service.list_pension_entries()` and `list_pension_types()` already handle this

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond what the roadmap and success criteria define — open to standard FastAPI patterns for router organisation and schema naming.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-core-data-api-routes*
*Context gathered: 2026-04-29*
