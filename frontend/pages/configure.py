"""Configure page — manage account types and liability types."""

import pandas as pd
import streamlit as st

from app.database import get_session
from app.services.account_service import list_account_types
from app.services.liability_service import list_liability_types
from app.services.type_service import (
    account_type_usage_count,
    create_account_type,
    create_liability_type,
    delete_account_type,
    delete_liability_type,
    liability_type_usage_count,
    rename_account_type,
    rename_liability_type,
)


def _get_user_id() -> str:
    return st.session_state["user_id"]


def _render_account_types(user_id: str) -> None:
    """Render account type management section."""
    session = next(get_session())
    try:
        account_types = list_account_types(session=session, user_id=user_id)
    finally:
        session.close()

    # Add new type
    with st.form("add_account_type", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_name = st.text_input("Add new account type", placeholder="e.g. Real Estate", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Add", use_container_width=True)
        if submitted and new_name:
            session = next(get_session())
            try:
                create_account_type(session=session, name=new_name, user_id=None)
                st.success(f"Added '{new_name}'")
                st.rerun()
            except Exception as e:
                st.error(str(e))
            finally:
                session.close()

    st.markdown("---")

    # Display types as a table
    if not account_types:
        st.info("No account types configured.")
        return

    # Build table data
    table_data = []
    for at in account_types:
        session = next(get_session())
        try:
            usage = account_type_usage_count(session=session, type_id=at.id)
        finally:
            session.close()
        table_data.append({
            "id": at.id,
            "Type Name": at.name,
            "Usage": f"{usage} account{'s' if usage != 1 else ''}",
            "can_delete": usage == 0
        })

    df = pd.DataFrame(table_data)

    # Display table with editable names
    edited_df = st.data_editor(
        df[["Type Name", "Usage"]],
        hide_index=True,
        use_container_width=True,
        disabled=["Usage"],
        key="account_types_table"
    )

    # Detect renames
    for idx, row in df.iterrows():
        old_name = row["Type Name"]
        new_name = edited_df.iloc[idx]["Type Name"]
        if old_name != new_name and new_name.strip():
            session = next(get_session())
            try:
                rename_account_type(session=session, type_id=row["id"], new_name=new_name)
                st.success(f"Renamed '{old_name}' to '{new_name}'")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            finally:
                session.close()

    # Delete section
    st.markdown("##### Delete Types")
    deletable_types = [row for row in table_data if row["can_delete"]]

    if deletable_types:
        to_delete = st.selectbox(
            "Select type to delete",
            options=[None] + [row["Type Name"] for row in deletable_types],
            format_func=lambda x: "Select a type..." if x is None else x,
            key="delete_account_type_select"
        )
        if to_delete and st.button("Delete Selected Type", key="delete_account_type_btn"):
            type_id = next(row["id"] for row in deletable_types if row["Type Name"] == to_delete)
            session = next(get_session())
            try:
                delete_account_type(session=session, type_id=type_id)
                st.success(f"Deleted '{to_delete}'")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            finally:
                session.close()
    else:
        st.caption("All types are in use and cannot be deleted.")


def _render_liability_types(user_id: str) -> None:
    """Render liability type management section."""
    session = next(get_session())
    try:
        liability_types = list_liability_types(session=session, user_id=user_id)
    finally:
        session.close()

    # Add new type
    with st.form("add_liability_type", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_name = st.text_input("Add new liability type", placeholder="e.g. Auto Loan", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Add", use_container_width=True)
        if submitted and new_name:
            session = next(get_session())
            try:
                create_liability_type(session=session, name=new_name, user_id=None)
                st.success(f"Added '{new_name}'")
                st.rerun()
            except Exception as e:
                st.error(str(e))
            finally:
                session.close()

    st.markdown("---")

    # Display types as a table
    if not liability_types:
        st.info("No liability types configured.")
        return

    # Build table data
    table_data = []
    for lt in liability_types:
        session = next(get_session())
        try:
            usage = liability_type_usage_count(session=session, type_id=lt.id)
        finally:
            session.close()
        table_data.append({
            "id": lt.id,
            "Type Name": lt.name,
            "Usage": f"{usage} liabilit{'ies' if usage != 1 else 'y'}",
            "can_delete": usage == 0
        })

    df = pd.DataFrame(table_data)

    # Display table with editable names
    edited_df = st.data_editor(
        df[["Type Name", "Usage"]],
        hide_index=True,
        use_container_width=True,
        disabled=["Usage"],
        key="liability_types_table"
    )

    # Detect renames
    for idx, row in df.iterrows():
        old_name = row["Type Name"]
        new_name = edited_df.iloc[idx]["Type Name"]
        if old_name != new_name and new_name.strip():
            session = next(get_session())
            try:
                rename_liability_type(session=session, type_id=row["id"], new_name=new_name)
                st.success(f"Renamed '{old_name}' to '{new_name}'")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            finally:
                session.close()

    # Delete section
    st.markdown("##### Delete Types")
    deletable_types = [row for row in table_data if row["can_delete"]]

    if deletable_types:
        to_delete = st.selectbox(
            "Select type to delete",
            options=[None] + [row["Type Name"] for row in deletable_types],
            format_func=lambda x: "Select a type..." if x is None else x,
            key="delete_liability_type_select"
        )
        if to_delete and st.button("Delete Selected Type", key="delete_liability_type_btn"):
            type_id = next(row["id"] for row in deletable_types if row["Type Name"] == to_delete)
            session = next(get_session())
            try:
                delete_liability_type(session=session, type_id=type_id)
                st.success(f"Deleted '{to_delete}'")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            finally:
                session.close()
    else:
        st.caption("All types are in use and cannot be deleted.")


def render() -> None:
    """Render the configure page."""
    st.header("Configure")
    user_id = _get_user_id()

    tab_accounts, tab_liabilities = st.tabs(["Account Types", "Liability Types"])

    with tab_accounts:
        _render_account_types(user_id)

    with tab_liabilities:
        _render_liability_types(user_id)
