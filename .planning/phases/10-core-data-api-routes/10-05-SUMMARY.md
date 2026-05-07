---
phase: 10-core-data-api-routes
plan: 05
status: complete
---

# Plan 10-05 Summary — Dashboard Router + All-Router Wiring

## What was built

**api/schemas/dashboard.py** — Pydantic schemas for the dashboard response:
- `MetricCards` (net_worth, assets, liabilities, net_worth_delta — all `float | None`)
- `TrendPoint` (date: str, net_worth, assets, liabilities — Recharts D-08 shape)
- `AllocationSlice` (name: str, value: float — Recharts D-09 pie slice)
- `PensionBar` (name: str, value: float — Recharts D-10 bar)
- `DashboardResponse` (cards + trend + allocation + pension)

**api/routers/dashboard.py** — `GET /api/dashboard`:
- Requires auth via `Depends(get_current_user)`
- trend: full snapshot history in ascending date order (from `get_snapshot_history`)
- cards: from latest snapshot; `net_worth_delta` = latest.net_worth − second-latest.net_worth
- allocation: latest balance per non-pension account type (first entry per type in DESC list)
- pension: same logic with pension types
- All Decimal values cast to float before serialisation

**api/main.py** — wired all six Phase 10 routers in this order:
```python
app.include_router(health.router)
app.include_router(accounts.router)
app.include_router(liabilities.router)
app.include_router(pension.router)
app.include_router(snapshots.router)
app.include_router(configure.router)
app.include_router(dashboard.router)
```
lifespan function and CORSMiddleware configuration preserved verbatim.

## Example dashboard response

```json
{
  "cards": {
    "net_worth": 10000.0,
    "assets": 10000.0,
    "liabilities": 0.0,
    "net_worth_delta": 500.0
  },
  "trend": [
    {"date": "2025-01-15", "net_worth": 9000.0, "assets": 9000.0, "liabilities": 0.0},
    {"date": "2025-02-15", "net_worth": 9500.0, "assets": 9500.0, "liabilities": 0.0},
    {"date": "2025-03-15", "net_worth": 10000.0, "assets": 10000.0, "liabilities": 0.0}
  ],
  "allocation": [
    {"name": "ISA", "value": 5000.0},
    {"name": "Brokerage", "value": 3000.0}
  ],
  "pension": [
    {"name": "SIPP", "value": 45000.0}
  ]
}
```

## net_worth_delta definition

`net_worth_delta = latest_snapshot.net_worth - second_latest_snapshot.net_worth`

Returns `null` if fewer than two snapshots exist or if either net_worth is null.

## Test results

- `tests/test_api_dashboard.py` — 7 tests, all green
- `tests/test_api_main_wiring.py` — 23 parametrized probes, all green
  - Uses `raise_server_exceptions=False` so DB errors return 500 rather than propagating — the test only cares about route registration (not 404), not endpoint correctness.
  - Distinguishes "route not registered" (404 with `{"detail": "Not Found"}`) from "resource not found" (404 with custom detail) via JSON body check.

## The 23-probe wiring test as a deployment check

`pytest tests/test_api_main_wiring.py` is the canonical "are all Phase 10 routes deployed?" check. It probes every prefix and asserts no route returns a `{"detail": "Not Found"}` 404. Run this in CI or post-deploy to confirm all routers are wired.

## Deviations from plan

- `raise_server_exceptions=False` added to wiring test's `TestClient` — required because `app.database.engine` is created at module import time from the first `DATABASE_URL` env var seen. In the full test suite, other test files set `DATABASE_URL=postgres:postgres` first, causing the wiring test's DB calls to fail. The `raise_server_exceptions=False` setting makes these return 500 (not raise), which still proves the route is registered.
- Dashboard test files use `TEST_DATABASE_URL` setdefault in addition to `DATABASE_URL` to ensure conftest.py picks up the correct credentials when the dashboard tests run in isolation.
