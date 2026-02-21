"""Liability management page — list, add, edit balance, deactivate."""

from decimal import Decimal, InvalidOperation

import streamlit as st

from app.database import get_session
from app.services.liability_service import (
    create_liability,
    deactivate_liability,
    list_liabilities,
    list_liability_types,
    update_balance,
)
from app.services.snapshot_service import capture_snapshot


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
    """Render the liabilities management page."""
    st.header("Liabilities")
    user_id = _get_user_id()

    session = next(get_session())
    try:
        liability_types = list_liability_types(session=session, user_id=user_id)
        liabilities = list_liabilities(session=session, user_id=user_id)
    finally:
        session.close()

    type_map = {lt.id: lt.name for lt in liability_types}

    # --- Add new liability ---
    st.subheader("Add Liability")
    with st.form("add_liability", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            liability_type = st.selectbox(
                "Type",
                options=liability_types,
                format_func=lambda lt: lt.name,
                key="new_liability_type",
            )
        with col2:
            liability_name = st.text_input("Name", placeholder="e.g. Home Mortgage")
        with col3:
            initial_balance = st.text_input("Balance", value="0.00")

        submitted = st.form_submit_button("Add Liability")
        if submitted and liability_name and liability_type:
            try:
                balance = Decimal(initial_balance)
            except InvalidOperation:
                st.error("Invalid balance amount.")
            else:
                session = next(get_session())
                try:
                    create_liability(
                        session=session,
                        user_id=user_id,
                        liability_type_id=liability_type.id,
                        name=liability_name,
                        balance=balance,
                    )
                    capture_snapshot(session=session, user_id=user_id)
                    st.success(f"Liability '{liability_name}' created.")
                    st.rerun()
                finally:
                    session.close()

    # --- List liabilities grouped by type ---
    st.subheader("Your Liabilities")

    if not liabilities:
        st.info("No liabilities yet. Add one above.")
        return

    grouped: dict[str, list] = {}
    for liab in liabilities:
        type_name = type_map.get(liab.liability_type_id, "Unknown")
        grouped.setdefault(type_name, []).append(liab)

    # Batch update form
    with st.form("batch_update_liabilities"):
        updates_to_process = []
        deactivations_to_process = []

        for type_name, type_liabilities in sorted(grouped.items()):
            st.markdown(f"**{type_name}**")
            for liab in type_liabilities:
                col_select, col_name, col_current, col_new, col_deactivate = st.columns(
                    [0.5, 2.5, 1.5, 1.5, 0.5]
                )
                with col_select:
                    selected = st.checkbox(
                        "Select",
                        key=f"liab_select_{liab.id}",
                        label_visibility="collapsed",
                    )
                with col_name:
                    st.text(liab.name)
                with col_current:
                    st.text(f"£{liab.balance:,.2f}")
                with col_new:
                    new_bal = st.text_input(
                        "New balance",
                        key=f"liab_bal_{liab.id}",
                        placeholder="New balance",
                        label_visibility="collapsed",
                    )
                with col_deactivate:
                    deactivate = st.checkbox(
                        "Deactivate",
                        key=f"liab_deactivate_{liab.id}",
                        label_visibility="collapsed",
                        help="Deactivate liability",
                    )

                if selected and new_bal:
                    updates_to_process.append((liab.id, new_bal))
                if deactivate:
                    deactivations_to_process.append(liab.id)

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
                for liability_id, balance_str in updates_to_process:
                    try:
                        parsed = Decimal(balance_str)
                        update_balance(
                            session=session,
                            liability_id=liability_id,
                            user_id=user_id,
                            new_balance=parsed,
                        )
                        success_count += 1
                    except InvalidOperation:
                        errors.append(f"Invalid balance for liability ID {liability_id}")

                # Process deactivations
                for liability_id in deactivations_to_process:
                    deactivate_liability(session=session, liability_id=liability_id, user_id=user_id)
                    success_count += 1

                if success_count > 0:
                    capture_snapshot(session=session, user_id=user_id)

                if errors:
                    for error in errors:
                        st.error(error)
                if success_count > 0:
                    st.success(f"Updated {success_count} liability/liabilities.")
                    st.rerun()
            finally:
                session.close()

    total = sum(lb.balance for lb in liabilities)
    st.metric("Total Liabilities", f"£{total:,.2f}")
