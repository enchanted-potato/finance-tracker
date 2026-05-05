# Phase 10: Core Data API Routes - Research

**Researched:** 2026-05-05
**Domain:** FastAPI route handlers, Pydantic v2 response schemas, CSV streaming, multipart upload
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** History endpoints return array grouped by date with `date`, `total`, `entries[]` shape (newest first).
- **D-02:** `entry_id` included in each history entry item for React delete/edit targeting.
- **D-03:** `total` is computed server-side (not by the client). Newest dates first.
- **D-04:** Every balance write (POST/PUT to entries) auto-calls `capture_snapshot()` for the entry's date. No separate endpoint needed.
- **D-05:** Monetary values as JSON numbers (floats), not strings.
- **D-06:** Pydantic schemas use `float` (not `Decimal`) for response models. Request bodies accept `float`.
- **D-07:** `GET /api/dashboard` included in Phase 10 before any React work.
- **D-08:** Recharts trend format: one object per date — `[{"date": "2025-01-15", "net_worth": 24000.50, "assets": 25000.50, "liabilities": 1000.00}]`.
- **D-09:** Allocation data: one slice per asset type `[{"name": "ISA", "value": 15000.00}]`.
- **D-10:** Pension data: one bar per provider `[{"name": "SIPP", "value": 45000.00}]`.
- **D-11:** `GET /api/account-types` and `GET /api/liability-types` include `in_use: bool` per type (using `account_type_usage_count()` / `liability_type_usage_count()`).
- **D-12:** DELETE on in-use type returns HTTP 409 Conflict; `ValueError` from service is mapped to 409.
- **D-13:** Pension = filtered accounts (`is_pension=True`). Separate routes under `/api/pension/` mirror accounts. Internally calls same service functions.
- **D-14:** `GET /api/snapshots/export.csv` returns `StreamingResponse` with `Content-Disposition: attachment; filename=snapshots.csv`.
- **D-15:** `POST /api/snapshots/import` accepts multipart `UploadFile`. Returns `{imported, skipped, errors}`.
- **D-16:** `GET /api/snapshots` returns history list ordered ascending by date.

### Claude's Discretion

- Exact URL path naming (e.g. `/entries` vs `/balance-entries`)
- Schema field ordering and optional fields on request bodies
- Router file structure under `api/routers/`
- How to handle `DELETE /api/snapshots/{id}` (service exists)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-05 | Endpoints for account CRUD, date-aware balance entry, and entry history (daily totals + per-account breakdown computed server-side) | Service functions fully inspected; thin-router pattern established; history grouping logic documented |
| API-06 | Endpoints for liability CRUD, date-aware balance entry, and entry history (daily totals + per-liability breakdown computed server-side) | `list_liability_entries()` returns flat list; router must group by date; service raises `ValueError` on not-found |
| API-07 | Endpoints for pension CRUD, date-aware balance entry, and entry history (daily totals + per-provider breakdown computed server-side) | `list_pension_entries()` and `list_pension_types()` already exist; pension router mirrors accounts router with pension filter |
| API-08 | Endpoints for snapshot history list, CSV export (StreamingResponse), CSV import (multipart UploadFile), and account/liability type CRUD with safe delete | `import_csv_snapshots()` already returns `(imported, skipped, errors)` tuple; CSV generation must be built in router; type delete raises `ValueError` mapped to 409 |
</phase_requirements>

## Summary

Phase 10 is a translation layer task: the service functions are complete and correct; the work is writing thin route handlers, Pydantic response schemas, and a small amount of in-router data shaping (date grouping for history, CSV generation for export, Recharts shaping for dashboard). No business logic belongs in routes.

The project already has the FastAPI foundation (main.py, dependencies.py, health router) from Phase 9. The established pattern — one router file per domain in `api/routers/`, one schema file per domain in `api/schemas/`, `Depends(get_current_user)` + `Depends(get_session)` on all protected endpoints — just needs to be replicated six times (accounts, liabilities, pension, snapshots, configure/types, dashboard).

The two non-trivial pieces are: (1) grouping flat service results by date for history endpoints (pure Python, no DB query), and (2) generating the CSV bytes for `GET /api/snapshots/export.csv` using Python's `csv` module and wrapping them in `StreamingResponse`.

**Primary recommendation:** Follow the `api/routers/health.py` pattern exactly. One router file per domain. All shaping (date grouping, Recharts format, CSV bytes) happens in the router function body after the service call — it is still thin because it is data transformation, not business logic.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | ≥0.136.1 (already installed) | Route handlers, dependency injection, OpenAPI | Already in project |
| Pydantic v2 | Ships with FastAPI | Response schemas, request validation | Already in project |
| SQLModel | Already installed | ORM — services return SQLModel objects | Already in project |
| `fastapi.responses.StreamingResponse` | Built-in | CSV file download | Part of FastAPI stdlib |
| `fastapi.UploadFile` | Built-in | Multipart CSV import | Part of FastAPI stdlib |
| Python `csv` + `io.StringIO` / `io.BytesIO` | stdlib | Generate CSV bytes for export | No extra dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` + `fastapi.testclient.TestClient` | Already installed | API route tests | All route tests |
| `pytest-mock` | Already installed | Mocking `capture_snapshot` in route tests | When isolating service calls |
| `unittest.mock.patch.object` | stdlib | Override `settings.dev_user_id` in tests | Auth bypass pattern already used in Phase 9 tests |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python `csv` for export | pandas `to_csv()` | pandas already in project but adds import cost; stdlib csv is sufficient for a simple flat export |
| Flat `list[EntryResponse]` for history | Grouping in router | Grouping in router keeps React dumb — matches architecture constraint |

**Installation:** No new packages required. All dependencies already present.

## Architecture Patterns

### Recommended Project Structure

```
api/
├── main.py                  # Add include_router() calls here
├── dependencies.py          # get_current_user — unchanged
├── routers/
│   ├── health.py            # Existing example
│   ├── accounts.py          # NEW
│   ├── liabilities.py       # NEW
│   ├── pension.py           # NEW
│   ├── snapshots.py         # NEW (includes export.csv + import + history list + delete)
│   ├── configure.py         # NEW (account-types + liability-types CRUD)
│   └── dashboard.py         # NEW
└── schemas/
    ├── health.py            # Existing example
    ├── accounts.py          # NEW
    ├── liabilities.py       # NEW
    ├── pension.py           # NEW (may reuse account schemas)
    ├── snapshots.py         # NEW
    ├── configure.py         # NEW
    └── dashboard.py         # NEW
```

### Pattern 1: Thin Router (established in health.py)

**What:** Router function calls one or more service functions, maps results to Pydantic schema, returns.
**When to use:** Every route handler in Phase 10.

```python
# api/routers/accounts.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.services import account_service
from api.dependencies import get_current_user
from api.schemas.accounts import AccountTypeResponse, AccountEntryRequest, AccountEntryResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

@router.get("/types", response_model=list[AccountTypeResponse])
def list_account_types(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[AccountTypeResponse]:
    types = account_service.list_account_types(session=session, user_id=user_id)
    return [AccountTypeResponse.from_orm_with_usage(t, session) for t in types]
```

### Pattern 2: Pydantic Response Schema (float, no user_id leakage)

**What:** Separate `BaseModel` with `float` fields. Never expose `Decimal` or `user_id`.
**When to use:** Every response schema in Phase 10.

```python
# api/schemas/accounts.py
from pydantic import BaseModel
from datetime import date

class AccountTypeResponse(BaseModel):
    id: int
    name: str
    is_pension: bool
    in_use: bool  # computed in router from account_type_usage_count()

class EntryItemResponse(BaseModel):
    entry_id: int
    type_id: int
    type_name: str
    balance: float  # NOT Decimal

class HistoryDayResponse(BaseModel):
    date: str          # ISO format "2025-01-15"
    total: float
    entries: list[EntryItemResponse]

class AccountEntryRequest(BaseModel):
    account_type_id: int
    entry_date: date
    balance: float
    currency: str = "GBP"
    exchange_rate: float = 1.0
```

### Pattern 3: Date-Grouping for History Endpoints

**What:** Service returns a flat `list[AccountEntry]` sorted newest-first. Router groups by date into the D-01 shape.
**When to use:** `GET /api/accounts/history`, `GET /api/liabilities/history`, `GET /api/pension/history`.

```python
# In accounts.py router
from collections import defaultdict
from decimal import Decimal

@router.get("/history", response_model=list[HistoryDayResponse])
def get_account_history(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[HistoryDayResponse]:
    # Service returns AccountEntry objects with .account_type_id but not .type_name
    # Need to join type names — either enrich in router or add a service helper
    entries = account_service.list_non_pension_entries(session=session, user_id=user_id)
    types = {t.id: t.name for t in account_service.list_account_types(session=session, user_id=user_id)}

    grouped: dict[str, list] = defaultdict(list)
    totals: dict[str, float] = defaultdict(float)
    for e in entries:
        day = str(e.entry_date)
        grouped[day].append(EntryItemResponse(
            entry_id=e.id,
            type_id=e.account_type_id,
            type_name=types.get(e.account_type_id, ""),
            balance=float(e.balance * e.exchange_rate),
        ))
        totals[day] += float(e.balance * e.exchange_rate)

    return [
        HistoryDayResponse(date=day, total=totals[day], entries=grouped[day])
        for day in sorted(grouped.keys(), reverse=True)
    ]
```

**Key insight:** `list_account_entries()` and `list_non_pension_entries()` do NOT return type names — they return `AccountEntry` which has `account_type_id` only. The router must resolve names from `list_account_types()`. This is a data shaping concern, not business logic — it belongs in the router.

### Pattern 4: ValueError → 409 Conflict Mapping

**What:** Service raises `ValueError` when deleting an in-use type. Router catches and re-raises as HTTPException(409).
**When to use:** DELETE on account-types and liability-types.

```python
@router.delete("/account-types/{type_id}", status_code=204)
def delete_account_type(
    type_id: int,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> None:
    try:
        type_service.delete_account_type(session=session, type_id=type_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
```

**Note:** `delete_account_type()` does NOT filter by `user_id` — it finds by `type_id` only. The router should add an ownership check before calling it, OR accept that system-default types (user_id=None) are visible to all users. Given the single-user app design, the current behavior is acceptable.

### Pattern 5: StreamingResponse for CSV Export

**What:** Generate CSV bytes in-memory using `csv.writer`, wrap in `StreamingResponse`.
**When to use:** `GET /api/snapshots/export.csv`.

```python
import csv
import io
from fastapi.responses import StreamingResponse

@router.get("/export.csv")
def export_snapshots_csv(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
):
    snapshots = snapshot_service.get_snapshot_history(session=session, user_id=user_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "total_assets", "total_liabilities", "net_worth"])
    for s in snapshots:
        writer.writerow([
            s.snapshot_date.date().isoformat(),
            float(s.total_assets) if s.total_assets is not None else "",
            float(s.total_liabilities) if s.total_liabilities is not None else "",
            float(s.net_worth) if s.net_worth is not None else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=snapshots.csv"},
    )
```

### Pattern 6: UploadFile for CSV Import

**What:** Accept `UploadFile`, read bytes, decode to string, pass to service.
**When to use:** `POST /api/snapshots/import`.

```python
from fastapi import UploadFile, File

@router.post("/import")
async def import_snapshots_csv(
    file: UploadFile = File(...),
    session: Annotated[Session, Depends(get_session)] = ...,
    user_id: Annotated[str, Depends(get_current_user)] = ...,
):
    content = await file.read()
    file_str = content.decode("utf-8")
    imported, skipped, errors = snapshot_service.import_csv_snapshots(
        session=session, user_id=user_id, file_content=file_str
    )
    return {"imported": imported, "skipped": skipped, "errors": errors}
```

**Note:** The endpoint must be `async def` when using `await file.read()`. Other endpoints can be regular `def`.

### Pattern 7: Auto-Snapshot on Balance Write (D-04)

**What:** After every successful upsert, call `capture_snapshot()` for the entry's date.
**When to use:** All POST/PUT balance entry endpoints.

```python
@router.post("/entries", response_model=AccountEntryResponse, status_code=201)
def create_account_entry(
    body: AccountEntryRequest,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> AccountEntryResponse:
    entry = account_service.upsert_account_entry(
        session=session,
        user_id=user_id,
        account_type_id=body.account_type_id,
        entry_date=body.entry_date,
        balance=Decimal(str(body.balance)),
        currency=body.currency,
        exchange_rate=Decimal(str(body.exchange_rate)),
    )
    # D-04: Auto-snapshot after every balance write
    snapshot_service.capture_snapshot(session=session, user_id=user_id, snapshot_date=entry.entry_date)
    return AccountEntryResponse(
        id=entry.id,
        account_type_id=entry.account_type_id,
        entry_date=entry.entry_date,
        balance=float(entry.balance),
        currency=entry.currency,
    )
```

**Critical:** Service functions accept `Decimal` but request bodies provide `float`. Convert with `Decimal(str(body.balance))` — NOT `Decimal(body.balance)` which loses precision for floats.

### Pattern 8: Dashboard Recharts Shaping

**What:** Pull latest snapshot, compute allocation from account entries, return Recharts-format arrays.
**When to use:** `GET /api/dashboard`.

The dashboard endpoint must:
1. Call `get_latest_snapshot()` for metric cards
2. Call `get_snapshot_history()` for trend data
3. Call `list_non_pension_entries()` + `list_account_types()` for current allocation per type
4. Call `list_pension_types()` + `list_pension_entries()` for pension bars

Trend data (D-08): Iterate snapshots ordered ASC, build one dict per snapshot date.

```python
trend = [
    {
        "date": s.snapshot_date.date().isoformat(),
        "net_worth": float(s.net_worth) if s.net_worth is not None else None,
        "assets": float(s.total_assets) if s.total_assets is not None else None,
        "liabilities": float(s.total_liabilities) if s.total_liabilities is not None else None,
    }
    for s in snapshots  # ordered ASC from get_snapshot_history()
]
```

### Anti-Patterns to Avoid

- **Returning SQLModel models directly:** FastAPI will serialise `Decimal` fields as strings, not JSON numbers. Always return Pydantic `BaseModel` instances with `float` fields.
- **`response_model=AccountEntry`:** Exposes `user_id` to the client. Always use a dedicated response schema.
- **`Decimal(body.balance)` without `str()` intermediate:** `Decimal(0.1)` gives `Decimal('0.1000000000000000055511151231257827021181583404541015625')`. Use `Decimal(str(body.balance))`.
- **Forgetting `app.include_router()`:** New routers in `api/routers/` are invisible until added to `api/main.py`.
- **`async def` without `await`:** UploadFile's `.read()` is a coroutine — endpoint must be `async def`. Other endpoints should stay as regular `def` (FastAPI runs them in a thread pool).
- **Mixing `response_model` with `StreamingResponse`:** `GET /export.csv` must NOT have `response_model` set — FastAPI cannot validate StreamingResponse against a Pydantic model.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV generation | Custom string concatenation | `csv.writer` (stdlib) | Handles quoting, escaping, newlines correctly |
| CSV parsing for import | Custom parser | `snapshot_service.import_csv_snapshots()` | Already complete and tested |
| Auth token verification | Custom Firebase SDK calls | `api/dependencies.get_current_user` | Already written and tested in Phase 9 |
| DB session management | Manual session lifecycle | `Depends(get_session)` from `app/database.py` | Already provides rollback-on-exception |
| In-use type checking | Custom SQL query | `type_service.account_type_usage_count()` / `liability_type_usage_count()` | Already written |
| Snapshot capture | Custom snapshot logic | `snapshot_service.capture_snapshot()` | Already handles upsert, detail_json, pension separation |
| History grouping SQL | GROUP BY query | Python `defaultdict` in router | Services already return flat sorted lists; grouping is trivial data shaping |

**Key insight:** The services layer is complete. The only work is: schemas + thin routers + include_router() calls.

## Common Pitfalls

### Pitfall 1: Forgetting include_router() in main.py
**What goes wrong:** Router file created, endpoints registered in it, but HTTP calls return 404.
**Why it happens:** FastAPI does not auto-discover router files.
**How to avoid:** For each new router file, add `app.include_router(router_module.router)` to `api/main.py` immediately.
**Warning signs:** All tests for a new router return 404.

### Pitfall 2: Decimal fields reaching JSON serialisation
**What goes wrong:** Response contains `"balance": "1250.50"` (string) instead of `"balance": 1250.50` (number).
**Why it happens:** SQLModel models have `Decimal` fields. If `response_model=AccountEntry` is used, FastAPI serialises `Decimal` as string by default.
**How to avoid:** Always use a separate Pydantic `BaseModel` with `float` for response schemas. Never use SQLModel table models as response models.
**Warning signs:** JavaScript `parseFloat(response.balance)` needed in React — that means the API is broken.

### Pitfall 3: user_id in responses
**What goes wrong:** Client receives `{"id": 1, "user_id": "firebase-uid-abc", "balance": 1250.50}`.
**Why it happens:** SQLModel model returned directly or included in response schema.
**How to avoid:** Response schemas never include `user_id`. Check every schema field list before shipping.
**Warning signs:** Any API test asserting JSON keys finds `user_id` in response.

### Pitfall 4: Decimal(float) precision loss
**What goes wrong:** `upsert_account_entry()` stores `Decimal('0.10000000000000001')` instead of `Decimal('0.1')`.
**Why it happens:** `Decimal(0.1)` captures float's binary representation. `Decimal(str(0.1))` gives `Decimal('0.1')`.
**How to avoid:** Always convert: `Decimal(str(body.balance))` and `Decimal(str(body.exchange_rate))`.
**Warning signs:** Stored values have 15+ decimal places when inspected in DB.

### Pitfall 5: History endpoint missing type names
**What goes wrong:** `entries[].type_name` is always empty string.
**Why it happens:** `list_account_entries()` returns `AccountEntry` objects which have only `account_type_id`, not `type_name`. Forgetting to call `list_account_types()` for the lookup dict.
**How to avoid:** History router always calls both `list_*_entries()` AND `list_*_types()` to build a `{id: name}` map.
**Warning signs:** All entries in history response have `"type_name": ""`.

### Pitfall 6: StreamingResponse with response_model set
**What goes wrong:** FastAPI tries to validate the StreamingResponse object against a Pydantic model and raises a serialisation error.
**Why it happens:** `@router.get("/export.csv", response_model=SomeSchema)` conflicts with returning a `StreamingResponse`.
**How to avoid:** Do NOT set `response_model` on the CSV export endpoint.
**Warning signs:** `ResponseValidationError` in logs when calling export endpoint.

### Pitfall 7: Snapshot date type mismatch
**What goes wrong:** `capture_snapshot()` is called with the wrong type — `snapshot_date` must be `datetime.date`, but `Snapshot.snapshot_date` is stored as `datetime`.
**Why it happens:** `capture_snapshot()` accepts `date | None` and internally converts to `datetime`. Passing a `datetime` instead of `date` triggers the `if snapshot_date is None` guard to be skipped but then `datetime.combine(snapshot_date, ...)` fails because `snapshot_date` is already a datetime.
**How to avoid:** Call `capture_snapshot(snapshot_date=entry.entry_date)` where `entry.entry_date` is `date_type`. Do not pass `entry.snapshot_date` (which is `datetime`) from Snapshot objects.
**Warning signs:** TypeError in snapshot capture after balance writes.

### Pitfall 8: UploadFile endpoint must be async def
**What goes wrong:** `await file.read()` in a regular (sync) `def` function raises `RuntimeError`.
**Why it happens:** `UploadFile.read()` is a coroutine in FastAPI.
**How to avoid:** Import endpoint must be declared `async def`.
**Warning signs:** `RuntimeError: coroutine was never awaited`.

## Code Examples

### Router Registration (main.py)

```python
# api/main.py — add these after health router
from api.routers import accounts, liabilities, pension, snapshots, configure, dashboard

app.include_router(accounts.router)
app.include_router(liabilities.router)
app.include_router(pension.router)
app.include_router(snapshots.router)
app.include_router(configure.router)
app.include_router(dashboard.router)
```

### Schema with in_use Flag

```python
# api/schemas/configure.py
from pydantic import BaseModel

class AccountTypeResponse(BaseModel):
    id: int
    name: str
    is_pension: bool
    in_use: bool

class LiabilityTypeResponse(BaseModel):
    id: int
    name: str
    in_use: bool

class TypeCreateRequest(BaseModel):
    name: str
    is_pension: bool = False  # Only for account types

class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
```

### Test Pattern (TestClient with DEV_USER_ID bypass)

```python
# tests/test_api_accounts.py
import os
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finance_tracker_test")
os.environ.setdefault("DEV_USER_ID", "test-dev-user")

import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def client():
    from api.main import app
    with TestClient(app) as c:
        yield c

def test_list_account_types_returns_200(client):
    response = client.get("/api/accounts/types")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    for item in response.json():
        assert "user_id" not in item
        assert isinstance(item["in_use"], bool)
```

### DELETE returns 409 on in-use type

```python
def test_delete_in_use_type_returns_409(client, db_session):
    # Assumes type is in use
    response = client.delete("/api/account-types/1")  # adjust to real seeded ID
    assert response.status_code == 409
```

### Dashboard Schema Shape

```python
# api/schemas/dashboard.py
from pydantic import BaseModel
from typing import Optional

class TrendPoint(BaseModel):
    date: str
    net_worth: Optional[float]
    assets: Optional[float]
    liabilities: Optional[float]

class AllocationSlice(BaseModel):
    name: str
    value: float

class PensionBar(BaseModel):
    name: str
    value: float

class MetricCards(BaseModel):
    net_worth: Optional[float]
    assets: Optional[float]
    liabilities: Optional[float]
    net_worth_delta: Optional[float]  # vs previous snapshot

class DashboardResponse(BaseModel):
    cards: MetricCards
    trend: list[TrendPoint]
    allocation: list[AllocationSlice]
    pension: list[PensionBar]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Returning SQLModel models from routes | Separate Pydantic `BaseModel` response schemas | Pydantic v2 / FastAPI 0.100+ | Required to control field serialisation (Decimal → float, exclude user_id) |
| `@router.get("/export", response_class=FileResponse)` | `StreamingResponse(iter([content]), ...)` | FastAPI 0.95+ | StreamingResponse is more flexible for in-memory content |
| `model_validate(orm_obj)` for ORM → Pydantic | Constructor with explicit field mapping | Pydantic v2 | Explicit mapping is clearer and avoids `model_config = ConfigDict(from_attributes=True)` boilerplate |

## Open Questions

1. **Dashboard: net_worth_delta definition**
   - What we know: D-08 covers trend data. Cards need a delta (RDASH-01 says "negative delta shown in red").
   - What's unclear: Delta = current vs previous snapshot? vs 30 days ago? vs same month last year?
   - Recommendation: Delta = net_worth of latest snapshot minus net_worth of second-latest snapshot. Simple and obvious to the user. Planner should document this as Claude's discretion.

2. **Pension history: type_name resolution**
   - What we know: `list_pension_entries()` returns `AccountEntry` objects. Type names need `list_account_types()` with pension filter.
   - What's unclear: Should the pension history router use `list_pension_types()` for the name map, or `list_account_types()` filtered by `is_pension`?
   - Recommendation: Use `list_pension_types()` — it already returns only pension account types. Build `{id: name}` map from it.

3. **`GET /api/account-types` vs `GET /api/accounts/types` URL structure**
   - What we know: Context says Claude's discretion on URL naming.
   - What's unclear: Two patterns exist in D-11 (uses `/api/account-types`) and D-13 (uses `/api/pension/types`).
   - Recommendation: Types endpoints under their domain prefix — `/api/accounts/types`, `/api/liabilities/types`, `/api/pension/types`. Configure page uses `GET /api/configure/account-types` and `GET /api/configure/liability-types` to avoid confusion. But since pension types ARE account types, `GET /api/pension/types` calls `list_pension_types()` filtered.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x + fastapi.testclient.TestClient |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_api_accounts.py tests/test_api_liabilities.py tests/test_api_pension.py tests/test_api_snapshots.py tests/test_api_configure.py tests/test_api_dashboard.py -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-05 | GET /api/accounts/types returns list with in_use bool, no user_id | integration | `pytest tests/test_api_accounts.py::test_list_account_types -x` | ❌ Wave 0 |
| API-05 | POST /api/accounts/entries creates entry and auto-captures snapshot | integration | `pytest tests/test_api_accounts.py::test_create_entry_auto_snapshot -x` | ❌ Wave 0 |
| API-05 | GET /api/accounts/history returns date-grouped array newest-first | integration | `pytest tests/test_api_accounts.py::test_account_history_shape -x` | ❌ Wave 0 |
| API-06 | POST /api/liabilities/entries creates entry and auto-captures snapshot | integration | `pytest tests/test_api_liabilities.py::test_create_liability_entry -x` | ❌ Wave 0 |
| API-06 | GET /api/liabilities/history returns date-grouped array with totals | integration | `pytest tests/test_api_liabilities.py::test_liability_history_shape -x` | ❌ Wave 0 |
| API-07 | GET /api/pension/types returns only pension account types | integration | `pytest tests/test_api_pension.py::test_pension_types_filtered -x` | ❌ Wave 0 |
| API-07 | GET /api/pension/history returns only pension entries grouped by date | integration | `pytest tests/test_api_pension.py::test_pension_history_shape -x` | ❌ Wave 0 |
| API-08 | DELETE /api/configure/account-types/{id} when in-use returns 409 | integration | `pytest tests/test_api_configure.py::test_delete_in_use_type_returns_409 -x` | ❌ Wave 0 |
| API-08 | GET /api/snapshots/export.csv returns text/csv with Content-Disposition | integration | `pytest tests/test_api_snapshots.py::test_export_csv_headers -x` | ❌ Wave 0 |
| API-08 | POST /api/snapshots/import returns {imported, skipped, errors} | integration | `pytest tests/test_api_snapshots.py::test_import_csv -x` | ❌ Wave 0 |
| API-04 (validation) | All money fields in responses are JSON numbers not strings | integration | `pytest tests/test_api_accounts.py::test_balance_is_float_not_string -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_api_health.py tests/test_api_auth.py -x` (existing green suite)
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_api_accounts.py` — covers API-05 (types list, entry create, history shape, float serialisation)
- [ ] `tests/test_api_liabilities.py` — covers API-06 (entry create, history shape)
- [ ] `tests/test_api_pension.py` — covers API-07 (types filtered, entries filtered, history shape)
- [ ] `tests/test_api_snapshots.py` — covers API-08 (export CSV headers, import result shape, history list)
- [ ] `tests/test_api_configure.py` — covers API-08 (type CRUD, 409 on in-use delete)
- [ ] `tests/test_api_dashboard.py` — covers API-04/API-05-07 integration (Recharts shapes)

Note: `tests/conftest.py` already provides `db_session`, `test_user`, `account_type`, `liability_type`, `make_account`, `make_liability` fixtures. New test files can import from it directly. No Wave 0 conftest work needed — existing fixtures are sufficient.

## Sources

### Primary (HIGH confidence)

- Codebase inspection: `api/main.py`, `api/dependencies.py`, `api/routers/health.py`, `api/schemas/health.py` — established patterns confirmed
- Codebase inspection: `app/services/account_service.py`, `app/services/liability_service.py`, `app/services/snapshot_service.py`, `app/services/type_service.py` — all service function signatures and return types confirmed
- Codebase inspection: `app/models.py` — all `Decimal` fields confirmed, `Snapshot.snapshot_date` is `datetime` (not `date`)
- Codebase inspection: `tests/test_api_health.py`, `tests/test_api_auth.py` — TestClient patterns, DEV_USER_ID bypass pattern confirmed
- Codebase inspection: `tests/conftest.py` — existing fixtures confirmed usable in new test files

### Secondary (MEDIUM confidence)

- FastAPI official docs pattern for `StreamingResponse` with CSV — well-established pattern, consistent with FastAPI 0.136.1 in project
- FastAPI official docs pattern for `UploadFile` multipart — `async def` + `await file.read()` is the documented approach
- Pydantic v2 `BaseModel` with `float` fields — verified by `tests/test_api_health.py` `test_decimal_serialises_as_float` which already proves this pattern works in this project

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, patterns already used in Phase 9
- Architecture: HIGH — patterns directly read from existing codebase files
- Pitfalls: HIGH — Decimal pitfalls confirmed by reading actual service function signatures; StreamingResponse pitfalls confirmed from FastAPI behavior
- History grouping pattern: HIGH — service return types directly confirmed; no SQL magic needed
- Dashboard shape: HIGH — D-08/09/10 locked in CONTEXT.md, snapshot_service functions confirmed

**Research date:** 2026-05-05
**Valid until:** 2026-06-05 (stable stack, no fast-moving dependencies)
