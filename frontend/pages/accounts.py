"""Account management page — list, add, edit balance, deactivate."""

from decimal import Decimal, InvalidOperation

import streamlit as st

from app.database import get_session
from app.services.account_service import (
    create_account,
    deactivate_account,
    list_account_types,
    list_accounts,
    update_balance,
)
from app.services.snapshot_service import capture_snapshot


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
    """Render the accounts management page."""
    st.header("Asset Accounts")
    user_id = _get_user_id()

    session = next(get_session())
    try:
        account_types = list_account_types(session=session, user_id=user_id)
        accounts = list_accounts(session=session, user_id=user_id)
    finally:
        session.close()

    type_map = {at.id: at.name for at in account_types}

    # --- Add new account ---
    st.subheader("Add Account")
    with st.form("add_account", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            account_type = st.selectbox(
                "Type",
                options=account_types,
                format_func=lambda at: at.name,
                key="new_account_type",
            )
        with col2:
            account_name = st.text_input("Name", placeholder="e.g. Chase Checking")
        with col3:
            initial_balance = st.text_input("Balance", value="0.00")

        submitted = st.form_submit_button("Add Account")
        if submitted and account_name and account_type:
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
                        account_type_id=account_type.id,
                        name=account_name,
                        balance=balance,
                    )
                    capture_snapshot(session=session, user_id=user_id)
                    st.success(f"Account '{account_name}' created.")
                    st.rerun()
                finally:
                    session.close()

    # --- List accounts grouped by type ---
    st.subheader("Your Accounts")

    if not accounts:
        st.info("No accounts yet. Add one above.")
        return

    # Group accounts by type
    grouped: dict[str, list] = {}
    for acct in accounts:
        type_name = type_map.get(acct.account_type_id, "Unknown")
        grouped.setdefault(type_name, []).append(acct)

    # Batch update form
    with st.form("batch_update_accounts"):
        updates_to_process = []
        deactivations_to_process = []

        for type_name, type_accounts in sorted(grouped.items()):
            st.markdown(f"**{type_name}**")
            for acct in type_accounts:
                col_select, col_name, col_current, col_new, col_deactivate = st.columns(
                    [0.5, 2.5, 1.5, 1.5, 0.5]
                )
                with col_select:
                    selected = st.checkbox(
                        "Select",
                        key=f"select_{acct.id}",
                        label_visibility="collapsed",
                    )
                with col_name:
                    st.text(acct.name)
                with col_current:
                    st.text(f"£{acct.balance:,.2f}")
                with col_new:
                    new_bal = st.text_input(
                        "New balance",
                        key=f"bal_{acct.id}",
                        placeholder="New balance",
                        label_visibility="collapsed",
                    )
                with col_deactivate:
                    deactivate = st.checkbox(
                        "Deactivate",
                        key=f"deactivate_{acct.id}",
                        label_visibility="collapsed",
                        help="Deactivate account",
                    )

                if selected and new_bal:
                    updates_to_process.append((acct.id, new_bal))
                if deactivate:
                    deactivations_to_process.append(acct.id)

            st.divider()

        # Submit button for batch update
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("Update Selected")

        if submitted:
            errors = []
            success_count = 0

            session = next(get_session())
            try:
                # Process updates
                for account_id, balance_str in updates_to_process:
                    try:
                        parsed = Decimal(balance_str)
                        update_balance(
                            session=session,
                            account_id=account_id,
                            user_id=user_id,
                            new_balance=parsed,
                        )
                        success_count += 1
                    except InvalidOperation:
                        errors.append(f"Invalid balance for account ID {account_id}")

                # Process deactivations
                for account_id in deactivations_to_process:
                    deactivate_account(session=session, account_id=account_id, user_id=user_id)
                    success_count += 1

                if success_count > 0:
                    capture_snapshot(session=session, user_id=user_id)

                if errors:
                    for error in errors:
                        st.error(error)
                if success_count > 0:
                    st.success(f"Updated {success_count} account(s).")
                    st.rerun()
            finally:
                session.close()

    # Show total
    total = sum(a.balance for a in accounts)
    st.metric("Total Assets", f"£{total:,.2f}")
