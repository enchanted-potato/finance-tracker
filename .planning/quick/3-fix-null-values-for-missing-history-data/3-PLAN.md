---
phase: quick-3
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/models.py
  - app/services/snapshot_service.py
  - frontend/pages/dashboard.py
  - frontend/pages/history.py
  - tests/test_snapshot_service.py
autonomous: true
requirements: []

must_haves:
  truths:
    - "Dashboard line chart shows a gap (missing point) for dates where liabilities were not entered"
    - "Dashboard line chart shows a gap (missing point) for dates where assets were not entered"
    - "History page displays '-' instead of '£0.00' when a value is NULL"
    - "Live-captured snapshots (from active accounts) continue to store real Decimal values"
    - "CSV import sets total_liabilities=NULL and net_worth=NULL when no liabilities column present"
  artifacts:
    - path: "app/models.py"
      provides: "Nullable Decimal fields on Snapshot model"
      contains: "Optional[Decimal]"
    - path: "app/services/snapshot_service.py"
      provides: "NULL assignment in import_csv_snapshots for missing columns"
    - path: "frontend/pages/dashboard.py"
      provides: "None-safe chart rendering that passes None through to Plotly"
    - path: "frontend/pages/history.py"
      provides: "None-safe table rendering"
  key_links:
    - from: "app/services/snapshot_service.py"
      to: "app/models.py"
      via: "Snapshot(total_liabilities=None)"
      pattern: "total_liabilities=None"
    - from: "frontend/pages/dashboard.py"
      to: "Snapshot.total_liabilities"
      via: "None-safe float conversion"
      pattern: "float.*if.*else None"
---

<objective>
Fix snapshot data so that missing assets or liabilities are stored as NULL (not 0) in the database, and displayed as chart gaps and dashes in the UI rather than misleading zero values.

Purpose: Imported historical snapshots often have only assets (no liabilities data). Storing 0 draws a false zero-line on the dashboard and shows £0.00 in History, misrepresenting the data.
Output: Nullable Snapshot fields, NULL-aware CSV import, gap-rendering dashboard chart, dash-rendering history table.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/quick/3-fix-null-values-for-missing-history-data/3-PLAN.md
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Make Snapshot fields nullable and update import logic</name>
  <files>app/models.py, app/services/snapshot_service.py, tests/test_snapshot_service.py</files>
  <behavior>
    - Test: import_csv_snapshots with a "Date,Value" CSV sets total_liabilities=None and net_worth=None on the created snapshot
    - Test: import_csv_snapshots with a full "Date,Total Assets,Total Liabilities,Net Worth" CSV still stores real Decimal values for all three fields
    - Test: capture_snapshot (live) still stores non-null Decimal values for all three fields even when accounts list is empty (stores Decimal("0"), not None)
    - Test: import_csv_liabilities recalculates net_worth as total_assets - total_liabilities even when original net_worth was None
  </behavior>
  <action>
    In app/models.py, change the three Snapshot numeric fields to Optional[Decimal] with no default:

    ```python
    total_assets: Decimal | None = Field(default=None, max_digits=14, decimal_places=2)
    total_liabilities: Decimal | None = Field(default=None, max_digits=14, decimal_places=2)
    net_worth: Decimal | None = Field(default=None, max_digits=14, decimal_places=2)
    ```

    This requires an Alembic migration OR a direct ALTER TABLE. Since this is a deployed Cloud SQL app with real data, generate a migration. Run:
    ```
    alembic revision --autogenerate -m "nullable_snapshot_fields"
    alembic upgrade head
    ```
    If Alembic is not configured, apply manually via psql:
    ```sql
    ALTER TABLE snapshots ALTER COLUMN total_assets DROP NOT NULL;
    ALTER TABLE snapshots ALTER COLUMN total_liabilities DROP NOT NULL;
    ALTER TABLE snapshots ALTER COLUMN net_worth DROP NOT NULL;
    ```
    NOTE: Existing rows with Decimal("0") are fine — they remain as 0, not NULL. Only newly imported snapshots with missing columns will be NULL.

    In app/services/snapshot_service.py, update import_csv_snapshots:
    - When only a value_col is detected (single-value CSV): set total_liabilities=None, net_worth=None (assets only)
    - When assets_col is present but liabilities_col is absent: set total_liabilities=None, net_worth=None
    - When all three columns present: keep existing logic (real Decimal values)
    - capture_snapshot is NOT changed — it always computes real totals from live accounts

    Update import_csv_liabilities: when recalculating net_worth, handle the case where existing.total_assets may be None (treat as Decimal("0") for the calculation).

    Write failing tests first, then implement.
  </action>
  <verify>
    <automated>pytest tests/test_snapshot_service.py -x -q</automated>
  </verify>
  <done>All snapshot service tests pass; NULL is stored for missing liabilities/net_worth on asset-only CSV imports; full-column imports still store real values.</done>
</task>

<task type="auto">
  <name>Task 2: Render NULL values as chart gaps and table dashes</name>
  <files>frontend/pages/dashboard.py, frontend/pages/history.py</files>
  <action>
    In frontend/pages/dashboard.py, update _render_line_chart to pass None through to Plotly:

    ```python
    def _render_line_chart(snapshots: list) -> None:
        dates = [s.snapshot_date.date() for s in snapshots]
        net_worth_values = [float(s.net_worth) if s.net_worth is not None else None for s in snapshots]
        assets_values = [float(s.total_assets) if s.total_assets is not None else None for s in snapshots]
        liabilities_values = [float(s.total_liabilities) if s.total_liabilities is not None else None for s in snapshots]
        ...
    ```

    Plotly Scatter traces with None in the y-list automatically render as gaps (missing points with no connecting line). No other chart changes needed.

    In frontend/pages/history.py, update the snapshot table render loop to guard against None values:

    - col_assets.text: replace `f"£{snap.total_assets:,.2f}"` with `f"£{snap.total_assets:,.2f}" if snap.total_assets is not None else "-"`
    - col_liab.text: same guard for snap.total_liabilities
    - col_nw.text: same guard for snap.net_worth
    - _format_change: update to handle None net_worth — if either current or previous is None, return "-"
    - The edit form number_input uses `value=float(snap.total_assets)` — guard: `value=float(snap.total_assets) if snap.total_assets is not None else 0.0` (same for liabilities)

    Also update _build_csv to handle None: emit empty string instead of str(None):
    ```python
    str(snap.total_assets) if snap.total_assets is not None else "",
    ```

    No automated test for Streamlit UI — verify manually by checking history page with a snapshot that has NULL liabilities.
  </action>
  <verify>
    <automated>python -c "import frontend.pages.dashboard; import frontend.pages.history; print('imports ok')"</automated>
  </verify>
  <done>Dashboard line chart renders gaps instead of zero points for NULL fields; History table shows '-' instead of '£0.00' for NULL fields; no TypeError or AttributeError on None values.</done>
</task>

</tasks>

<verification>
- pytest tests/test_snapshot_service.py passes with new NULL-behavior tests
- Dashboard chart shows gap (not zero) for snapshots missing liabilities
- History table shows '-' for null fields and does not crash
- Live snapshots (from accounts page update) still show real values
</verification>

<success_criteria>
- Snapshot model fields are Optional[Decimal]
- Asset-only CSV imports produce NULL total_liabilities and NULL net_worth
- Dashboard Plotly chart receives None for missing values (renders as gap)
- History table renders '-' for None values
- All existing snapshot service tests still pass
</success_criteria>

<output>
After completion, create `.planning/quick/3-fix-null-values-for-missing-history-data/3-SUMMARY.md`
</output>
