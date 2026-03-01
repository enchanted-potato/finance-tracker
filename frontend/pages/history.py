import csv
import io
from decimal import Decimal

import streamlit as st

from app.database import get_session
from app.services.snapshot_service import (
    delete_snapshot,
    get_snapshot_history,
    import_csv_snapshots,
    update_snapshot,
)


def _get_user_id() -> str:
    return st.session_state["user_id"]


def render() -> None:
    """Render the history page."""
    st.header("Net Worth History")
    user_id = _get_user_id()

    session = next(get_session())
    try:
        snapshots = get_snapshot_history(session=session, user_id=user_id)
    finally:
        session.close()

    if not snapshots:
        st.info(
            "No snapshots yet. Update an account or liability balance "
            "to create your first snapshot."
        )
        return

    # Reverse to show most recent first
    snapshots_desc = list(reversed(snapshots))

    # --- CSV import and export ---
    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(
            "📤 Import CSV",
            type=["csv"],
            help="Upload a CSV file with Date and Value columns to import historical snapshots",
        )
        csv_data = _build_csv(snapshots_desc)

    with col2:
        st.download_button(
            label="📥 Export CSV",
            data=csv_data,
            file_name="net_worth_history.csv",
            mime="text/csv",
            use_container_width=False,
        )


    # Handle file upload
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode("utf-8")
        session = next(get_session())
        try:
            imported, skipped, errors = import_csv_snapshots(
                session=session,
                user_id=user_id,
                file_content=file_content,
            )
            if errors:
                st.error(f"Import completed with errors:\n" + "\n".join(errors))
            else:
                st.success(
                    f"Import successful! {imported} snapshots imported, "
                    f"{skipped} skipped (already exist)."
                )
            st.rerun()
        finally:
            session.close()

    st.markdown("---")

    # --- Snapshot table ---
    for i, snap in enumerate(snapshots_desc):
        previous_nw = snapshots_desc[i + 1].net_worth if i + 1 < len(snapshots_desc) else None
        change = _format_change(snap.net_worth, previous_nw)

        col_date, col_assets, col_liab, col_nw, col_change, col_details = st.columns([2, 2, 2, 2, 2, 1])
        if i == 0:
            col_date.markdown("**Date**")
            col_assets.markdown("**Assets**")
            col_liab.markdown("**Liabilities**")
            col_nw.markdown("**Net Worth**")
            col_change.markdown("**Change**")
            col_details.markdown("")
            col_date, col_assets, col_liab, col_nw, col_change, col_details = st.columns([2, 2, 2, 2, 2, 1])

        col_date.text(snap.snapshot_date.strftime("%Y-%m-%d"))
        col_assets.text(f"£{snap.total_assets:,.2f}")
        col_liab.text(f"£{snap.total_liabilities:,.2f}")
        col_nw.text(f"£{snap.net_worth:,.2f}")
        col_change.text(change)

        show_key = f"show_{snap.id}"
        if show_key not in st.session_state:
            st.session_state[show_key] = False
        if col_details.button("Edit", key=f"btn_{snap.id}", use_container_width=True):
            st.session_state[show_key] = not st.session_state[show_key]

        if st.session_state[show_key]:
            with st.container():
                with st.form(key=f"edit_form_{snap.id}"):
                    new_assets = st.number_input(
                        "Total Assets",
                        value=float(snap.total_assets),
                        step=0.01,
                        format="%.2f",
                    )
                    new_liabilities = st.number_input(
                        "Total Liabilities",
                        value=float(snap.total_liabilities),
                        step=0.01,
                        format="%.2f",
                    )

                    col_save, col_delete = st.columns([1, 1])
                    with col_save:
                        if st.form_submit_button("Save"):
                            session = next(get_session())
                            try:
                                update_snapshot(
                                    session=session,
                                    snapshot_id=snap.id,
                                    total_assets=Decimal(str(new_assets)),
                                    total_liabilities=Decimal(str(new_liabilities)),
                                )
                                st.session_state[show_key] = False
                                st.rerun()
                            finally:
                                session.close()
                    with col_delete:
                        if st.form_submit_button("🗑️ Delete", type="secondary"):
                            session = next(get_session())
                            try:
                                delete_snapshot(session=session, snapshot_id=snap.id, user_id=user_id)
                                st.rerun()
                            finally:
                                session.close()

                if snap.detail_json:
                    detail = snap.detail_json
                    if detail.get("accounts"):
                        st.markdown("**Accounts**")
                        for acct in detail["accounts"]:
                            st.text(f"  {acct['name']}: £{Decimal(acct['balance']):,.2f}")
                    if detail.get("liabilities"):
                        st.markdown("**Liabilities**")
                        for liab in detail["liabilities"]:
                            st.text(f"  {liab['name']}: £{Decimal(liab['balance']):,.2f}")


def _format_change(current: Decimal, previous: Decimal | None) -> str:
    """Format the change from previous snapshot."""
    if previous is None:
        return "-"
    delta = current - previous
    if delta >= 0:
        return f"+£{delta:,.2f}"
    return f"-£{abs(delta):,.2f}"


def _build_csv(snapshots: list) -> str:
    """Build CSV string from snapshot data."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Total Assets", "Total Liabilities", "Net Worth"])
    for snap in snapshots:
        writer.writerow(
            [
                snap.snapshot_date.strftime("%Y-%m-%d"),
                str(snap.total_assets),
                str(snap.total_liabilities),
                str(snap.net_worth),
            ]
        )
    return output.getvalue()
