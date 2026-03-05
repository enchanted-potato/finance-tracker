"""Pension account management — list, add, edit balance, deactivate."""

from decimal import Decimal, InvalidOperation

import streamlit as st

from app.database import get_session
from app.services.account_service import (
    _get_pension_type_id,
    create_account,
    deactivate_account,
    list_account_types,
    list_pension_accounts,
    update_balance,
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
