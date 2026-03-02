---
phase: quick-1-pension
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/services/account_service.py
  - app/services/snapshot_service.py
  - frontend/pages/dashboard.py
  - frontend/pages/pension.py
  - frontend/main.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Pension accounts are excluded from Total Assets and Net Worth on the dashboard"
    - "Dashboard shows a Total Pension metric after Total Liabilities"
    - "Dashboard shows a bar chart at the bottom with pension value broken down per provider (account name)"
    - "A Pension nav item leads to a dedicated page for adding and updating pension account balances"
    - "Snapshot capture excludes pension balances from total_assets and net_worth"
  artifacts:
    - path: "frontend/pages/pension.py"
      provides: "Pension management page (add, update, deactivate pension accounts)"
    - path: "app/services/account_service.py"
      provides: "list_pension_accounts() helper returning only Pension-typed accounts"
    - path: "frontend/pages/dashboard.py"
      provides: "Updated dashboard with pension metric + bar chart"
  key_links:
    - from: "frontend/pages/pension.py"
      to: "app/services/account_service.py"
      via: "list_pension_accounts, create_account, update_balance, deactivate_account"
    - from: "frontend/pages/dashboard.py"
      to: "app/services/account_service.py"
      via: "list_pension_accounts for pension bar chart data"
    - from: "app/services/snapshot_service.py"
      to: "account_types table"
      via: "JOIN or subquery to exclude Pension type from total_assets"
---

<objective>
Add pension as a first-class, separate category in the net worth tracker.

Purpose: Pension is long-term illiquid wealth that should be tracked separately from liquid assets. It must not inflate Total Assets or Net Worth on the dashboard, but should be visible as its own metric and chart.

Output:
- Pension accounts excluded from Total Assets and Net Worth (both live dashboard and snapshot capture)
- Dashboard: new "Total Pension" metric displayed after Total Liabilities
- Dashboard: bar chart at bottom showing each pension account (by name) and its value
- New "Pension" sidebar page: add/update/deactivate pension accounts (mirrors accounts.py pattern)
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/STATE.md

<!-- Key interfaces the executor needs — no codebase exploration required -->
<interfaces>
From app/models.py:
```python
class AccountType(SQLModel, table=True):
    __tablename__ = "account_types"
    id: int | None
    name: str  # "Pension" is a seeded system default (user_id=None)
    user_id: str | None  # None for system defaults

class Account(SQLModel, table=True):
    __tablename__ = "accounts"
    id: int | None
    user_id: str
    account_type_id: int  # FK -> account_types.id
    name: str             # e.g. "Vanguard SIPP", "Nest Pension"
    balance: Decimal
    currency: str         # default "GBP"
    is_active: bool
```

From app/services/account_service.py:
```python
def list_accounts(*, session, user_id, active_only=True) -> list[Account]
def list_account_types(*, session, user_id) -> list[AccountType]
def create_account(*, session, user_id, account_type_id, name, balance, currency) -> Account
def update_balance(*, session, account_id, user_id, new_balance) -> Account
def deactivate_account(*, session, account_id, user_id) -> Account
```

From app/services/snapshot_service.py — capture_snapshot currently:
```python
accounts = session.exec(select(Account).where(Account.user_id == user_id, Account.is_active.is_(True))).all()
total_assets = sum((a.balance for a in accounts), Decimal("0"))
# net_worth = total_assets - total_liabilities
```

From app/seed.py:
```python
DEFAULT_ACCOUNT_TYPES = ["Cash Savings", "Investment Account", "Crypto", "Pension", "Other"]
# "Pension" is seeded as a system AccountType with user_id=None
```

From frontend/pages/dashboard.py — render() currently:
```python
accounts = list_accounts(session=session, user_id=user_id)
total_assets = sum((a.balance for a in accounts), Decimal("0"))
# Displays: col1=Net Worth, col2=Total Assets, col3=Total Liabilities
# Bottom: asset pie + liability pie side by side
```

From frontend/main.py — navigation:
```python
pages = {"Dashboard": "📊", "Accounts": "💰", "Liabilities": "💳", "History": "📈", "Configure": "⚙️"}
# match st.session_state["selected_page"]: case "Dashboard": dashboard.render() ...
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Service layer — pension helpers and snapshot exclusion</name>
  <files>app/services/account_service.py, app/services/snapshot_service.py</files>
  <action>
**In app/services/account_service.py** — add `list_pension_accounts` and `list_non_pension_accounts` helpers:

```python
PENSION_TYPE_NAME = "Pension"

def _get_pension_type_id(session: Session, user_id: str) -> int | None:
    """Return the AccountType.id for 'Pension' visible to this user, or None."""
    from sqlmodel import select
    from app.models import AccountType
    statement = select(AccountType).where(
        (AccountType.name == PENSION_TYPE_NAME),
        (AccountType.user_id.is_(None)) | (AccountType.user_id == user_id),
    )
    at = session.exec(statement).first()
    return at.id if at else None


def list_pension_accounts(*, session: Session, user_id: str, active_only: bool = True) -> list[Account]:
    """List accounts whose type is 'Pension'."""
    pension_type_id = _get_pension_type_id(session, user_id)
    if pension_type_id is None:
        return []
    statement = select(Account).where(
        Account.user_id == user_id,
        Account.account_type_id == pension_type_id,
    )
    if active_only:
        statement = statement.where(Account.is_active.is_(True))
    statement = statement.order_by(Account.name)
    return list(session.exec(statement).all())


def list_non_pension_accounts(*, session: Session, user_id: str, active_only: bool = True) -> list[Account]:
    """List accounts whose type is NOT 'Pension' (used for Total Assets)."""
    pension_type_id = _get_pension_type_id(session, user_id)
    statement = select(Account).where(Account.user_id == user_id)
    if pension_type_id is not None:
        statement = statement.where(Account.account_type_id != pension_type_id)
    if active_only:
        statement = statement.where(Account.is_active.is_(True))
    statement = statement.order_by(Account.account_type_id, Account.name)
    return list(session.exec(statement).all())
```

**In app/services/snapshot_service.py** — update `capture_snapshot` to exclude pension from totals. Replace the existing account query and total_assets computation with:

```python
from app.services.account_service import _get_pension_type_id

# Inside capture_snapshot, replace the accounts query block:
pension_type_id = _get_pension_type_id(session, user_id)
all_accounts = list(
    session.exec(
        select(Account).where(Account.user_id == user_id, Account.is_active.is_(True))
    ).all()
)
# Split pension vs non-pension
pension_accounts = [a for a in all_accounts if pension_type_id and a.account_type_id == pension_type_id]
non_pension_accounts = [a for a in all_accounts if not (pension_type_id and a.account_type_id == pension_type_id)]

total_assets = sum((a.balance for a in non_pension_accounts), Decimal("0"))
total_pension = sum((a.balance for a in pension_accounts), Decimal("0"))
total_liabilities = sum((lb.balance for lb in liabilities), Decimal("0"))
net_worth = total_assets - total_liabilities

# Update detail to include pension breakdown
detail = {
    "accounts": [
        {"id": a.id, "name": a.name, "balance": str(a.balance), "type_id": a.account_type_id}
        for a in non_pension_accounts
    ],
    "pension_accounts": [
        {"id": a.id, "name": a.name, "balance": str(a.balance), "type_id": a.account_type_id}
        for a in pension_accounts
    ],
    "liabilities": [
        {"id": lb.id, "name": lb.name, "balance": str(lb.balance), "type_id": lb.liability_type_id}
        for lb in liabilities
    ],
}
```

Also store `total_pension` in the Snapshot model's `detail_json` as a top-level key: `detail["total_pension"] = str(total_pension)` — the Snapshot model columns `total_assets` and `net_worth` already exclude pension after this change.

Important: Do NOT add total_pension as a new Snapshot column — keep it in `detail_json` to avoid a DB migration.
  </action>
  <verify>
    <automated>cd /Users/kristiakarakatsani/Repos/finance-tracker && python -c "from app.services.account_service import list_pension_accounts, list_non_pension_accounts; print('imports OK')"</automated>
  </verify>
  <done>
- `list_pension_accounts`, `list_non_pension_accounts`, `_get_pension_type_id` exist in account_service.py
- `capture_snapshot` excludes pension accounts from `total_assets` and `net_worth`
- `detail_json` includes `pension_accounts` list and `total_pension` string key
  </done>
</task>

<task type="auto">
  <name>Task 2: Dashboard updates + Pension page + Navigation wiring</name>
  <files>frontend/pages/dashboard.py, frontend/pages/pension.py, frontend/main.py</files>
  <action>
**frontend/pages/dashboard.py** — three changes:

1. Import and use `list_non_pension_accounts` and `list_pension_accounts` instead of `list_accounts`:
```python
from app.services.account_service import list_non_pension_accounts, list_pension_accounts, list_account_types
# ...
accounts = list_non_pension_accounts(session=session, user_id=user_id)
pension_accounts = list_pension_accounts(session=session, user_id=user_id)
```

2. Update `total_assets` computation (already correct since `accounts` now excludes pension). Add `total_pension` computation and a 4th metric column:
```python
total_pension = sum((a.balance for a in pension_accounts), Decimal("0"))

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Net Worth", f"£{net_worth:,.2f}", delta=_net_worth_delta(all_snapshots, net_worth))
with col2:
    st.metric("Total Assets", f"£{total_assets:,.2f}")
with col3:
    st.metric("Total Liabilities", f"£{total_liabilities:,.2f}")
with col4:
    st.metric("Total Pension", f"£{total_pension:,.2f}")
```

3. Add `_render_pension_bar` function and call it at the bottom of `render()`, after the existing pie charts section:
```python
# At the bottom of render(), after the pie charts columns:
if pension_accounts:
    st.subheader("Pension Breakdown")
    _render_pension_bar(pension_accounts)
```

Add this function:
```python
def _render_pension_bar(pension_accounts: list) -> None:
    """Render a bar chart of pension value per provider (account name)."""
    names = [a.name for a in pension_accounts]
    values = [float(a.balance) for a in pension_accounts]

    fig = go.Figure(
        data=[
            go.Bar(
                x=names,
                y=values,
                marker_color="#A855F7",
                text=[f"£{v:,.0f}" for v in values],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        yaxis_title="Amount (£)",
        yaxis_tickformat="£,.0f",
        margin={"l": 60, "r": 20, "t": 20, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
```

Also update the fallback snapshot branch (when `total_assets == 0 and total_liabilities == 0`) — leave it as-is since it uses snapshot data, and pension is now excluded from `total_assets` in snapshots.

**frontend/pages/pension.py** — new file following the same pattern as accounts.py, but scoped to pension accounts only:

```python
"""Pension account management — list, add, edit balance, deactivate."""

from decimal import Decimal, InvalidOperation

import streamlit as st

from app.database import get_session
from app.services.account_service import (
    create_account,
    deactivate_account,
    list_account_types,
    list_pension_accounts,
    update_balance,
    _get_pension_type_id,
)
from app.services.snapshot_service import capture_snapshot


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
    """Render the pension management page."""
    st.header("Pension")
    user_id = _get_user_id()

    session = next(get_session())
    try:
        pension_type_id = _get_pension_type_id(session, user_id)
        pension_accounts = list_pension_accounts(session=session, user_id=user_id)
    finally:
        session.close()

    if pension_type_id is None:
        st.error("Pension account type not found. Please ensure the database is seeded.")
        return

    # --- Add new pension account ---
    st.subheader("Add Pension Provider")
    with st.form("add_pension", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            account_name = st.text_input("Provider name", placeholder="e.g. Nest, Vanguard SIPP")
        with col2:
            initial_balance = st.text_input("Balance", value="0.00")

        submitted = st.form_submit_button("Add Pension")
        if submitted and account_name:
            try:
                balance = Decimal(initial_balance)
            except InvalidOperation:
                st.error("Invalid balance amount.")
            else:
                session = next(get_session())
                try:
                    create_account(
                        session=session,
                        user_id=user_id,
                        account_type_id=pension_type_id,
                        name=account_name,
                        balance=balance,
                    )
                    capture_snapshot(session=session, user_id=user_id)
                    st.success(f"Pension provider '{account_name}' added.")
                    st.rerun()
                finally:
                    session.close()

    # --- List pension accounts ---
    st.subheader("Your Pension Providers")

    if not pension_accounts:
        st.info("No pension providers yet. Add one above.")
        return

    with st.form("batch_update_pensions"):
        updates_to_process = []
        deactivations_to_process = []

        for acct in pension_accounts:
            col_name, col_current, col_new, col_deactivate = st.columns([2.5, 1.5, 1.5, 0.5])
            with col_name:
                st.text(acct.name)
            with col_current:
                st.text(f"£{acct.balance:,.2f}")
            with col_new:
                new_bal = st.text_input(
                    "New balance",
                    key=f"pbal_{acct.id}",
                    placeholder="New balance",
                    label_visibility="collapsed",
                )
            with col_deactivate:
                deactivate = st.checkbox(
                    "Deactivate",
                    key=f"pdeactivate_{acct.id}",
                    label_visibility="collapsed",
                    help="Remove this pension provider",
                )
            if new_bal:
                updates_to_process.append((acct.id, new_bal))
            if deactivate:
                deactivations_to_process.append(acct.id)

        st.divider()
        submitted = st.form_submit_button("Update")

        if submitted:
            errors = []
            success_count = 0
            session = next(get_session())
            try:
                for account_id, balance_str in updates_to_process:
                    try:
                        parsed = Decimal(balance_str)
                        update_balance(session=session, account_id=account_id, user_id=user_id, new_balance=parsed)
                        success_count += 1
                    except InvalidOperation:
                        errors.append(f"Invalid balance for account ID {account_id}")
                for account_id in deactivations_to_process:
                    deactivate_account(session=session, account_id=account_id, user_id=user_id)
                    success_count += 1
                if success_count > 0:
                    capture_snapshot(session=session, user_id=user_id)
                if errors:
                    for error in errors:
                        st.error(error)
                if success_count > 0:
                    st.success(f"Updated {success_count} pension account(s).")
                    st.rerun()
            finally:
                session.close()

    total = sum(a.balance for a in pension_accounts)
    st.metric("Total Pension", f"£{total:,.2f}")
```

**frontend/main.py** — two changes:

1. Import the new pension page at the top with the other page imports:
```python
from frontend.pages import accounts, configure, dashboard, history, liabilities, pension
```

2. Add "Pension" to the `pages` dict (between Liabilities and History to keep it logical):
```python
pages = {
    "Dashboard": "📊",
    "Accounts": "💰",
    "Liabilities": "💳",
    "Pension": "🏦",
    "History": "📈",
    "Configure": "⚙️",
}
```

3. Add the case in the match statement:
```python
case "Pension":
    pension.render()
```

Also update the `accounts.py` page: it currently calls `list_accounts` which returns ALL accounts including pension. Change it to call `list_non_pension_accounts` so pension does not appear in the Asset Accounts page:
```python
# In frontend/pages/accounts.py, change import and usage:
from app.services.account_service import (
    create_account,
    deactivate_account,
    list_account_types,
    list_non_pension_accounts,
    update_balance,
)
# ...
accounts = list_non_pension_accounts(session=session, user_id=user_id)
```

Also: the "Add Account" form in accounts.py uses a selectbox for account type that currently includes "Pension". Filter it out so users can't add Pension accounts through the Accounts page. After loading `account_types`, filter:
```python
# After loading account_types:
non_pension_types = [at for at in account_types if at.name != "Pension"]
# Then use non_pension_types in the selectbox instead of account_types
```
  </action>
  <verify>
    <automated>cd /Users/kristiakarakatsani/Repos/finance-tracker && python -c "from frontend.pages import pension; from frontend.pages import dashboard; print('imports OK')"</automated>
  </verify>
  <done>
- pension.py exists and renders without import errors
- dashboard.py shows 4 metrics: Net Worth, Total Assets, Total Liabilities, Total Pension
- dashboard.py renders pension bar chart when pension accounts exist
- main.py has "Pension" nav item routing to pension.render()
- accounts.py excludes Pension type from account creation and account list
  </done>
</task>

</tasks>

<verification>
After both tasks complete, verify the full flow:
1. `python -c "from app.services.account_service import list_pension_accounts, list_non_pension_accounts; from frontend.pages import pension, dashboard; print('All imports OK')"` — passes with no errors
2. `pytest tests/` — existing tests pass (no regressions)
3. Start the app locally (`docker-compose up` or `python -m streamlit run frontend/main.py`) and confirm:
   - "Pension" appears in the sidebar
   - Pension page allows adding a provider with a balance
   - Dashboard shows Total Pension metric (4th column)
   - Dashboard shows Pension Breakdown bar chart if pension accounts exist
   - Pension balances do NOT appear in Total Assets metric
</verification>

<success_criteria>
- Pension accounts are separated from Total Assets in both live dashboard and snapshot captures
- Dashboard displays "Total Pension" as a 4th headline metric
- Dashboard shows a "Pension Breakdown" bar chart (per provider name) when pension accounts exist
- A dedicated Pension sidebar page enables adding/editing pension provider balances
- The Accounts page no longer shows or allows adding Pension-typed accounts
- Existing tests pass without modification
</success_criteria>

<output>
After completion, create `.planning/quick/1-add-pension-as-separate-category-with-de/1-SUMMARY.md` with what was built, files modified, and any decisions made.
</output>
