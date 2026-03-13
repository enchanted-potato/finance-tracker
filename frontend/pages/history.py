import csv
import io
from decimal import Decimal

import streamlit as st

from app.database import get_session
from app.services.snapshot_service import (
    delete_snapshot,
    get_snapshot_history,
    import_csv_liabilities,
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

    # Collapse to one row per month (latest snapshot in each month), most recent first
    snapshots_desc = _latest_per_month(snapshots)

    # --- CSV actions ---
    tab_export, tab_import_snaps, tab_import_liab = st.tabs(
        ["Export CSV", "Import Snapshots", "Import Liabilities"]
    )

    with tab_export:
        csv_data = _build_csv(snapshots_desc)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="net_worth_history.csv",
            mime="text/csv",
        )

    with tab_import_snaps:
        st.caption("Format: Date, Total Assets, Total Liabilities, Net Worth")
        col_tpl, col_upload = st.columns([1, 2])
        with col_tpl:
            template_snapshots = "Date,Total Assets,Total Liabilities,Net Worth\n2025-01-01,50000.00,10000.00,40000.00"
            st.download_button(
                label="Download template",
                data=template_snapshots,
                file_name="snapshots_template.csv",
                mime="text/csv",
                key="dl_snapshots_template",
            )
        with col_upload:
            uploaded_snapshots = st.file_uploader(
                "Upload CSV",
                type=["csv"],
                key="upload_snapshots",
                label_visibility="collapsed",
            )
        if uploaded_snapshots is not None:
            file_content = uploaded_snapshots.read().decode("utf-8")
            session = next(get_session())
            try:
                imported, skipped, errors = import_csv_snapshots(
                    session=session,
                    user_id=user_id,
                    file_content=file_content,
                )
                if errors:
                    st.error("Import completed with errors:\n" + "\n".join(errors))
                else:
                    st.success(
                        f"Import successful! {imported} snapshots imported, "
                        f"{skipped} skipped (already exist)."
                    )
                st.rerun()
            finally:
                session.close()

    with tab_import_liab:
        st.caption("Updates existing snapshots only — leaves assets unchanged")
        col_tpl2, col_upload2 = st.columns([1, 2])
        with col_tpl2:
            template_liabilities = "Date,Total Liabilities\n2025-01-01,0.00"
            st.download_button(
                label="Download template",
                data=template_liabilities,
                file_name="liabilities_template.csv",
                mime="text/csv",
                key="dl_liabilities_template",
            )
        with col_upload2:
            uploaded_liabilities = st.file_uploader(
                "Upload CSV",
                type=["csv"],
                key="upload_liabilities",
                label_visibility="collapsed",
            )
        if uploaded_liabilities is not None:
            file_content = uploaded_liabilities.read().decode("utf-8")
            session = next(get_session())
            try:
                updated, skipped, errors = import_csv_liabilities(
                    session=session,
                    user_id=user_id,
                    file_content=file_content,
                )
                if errors:
                    st.error("Import completed with errors:\n" + "\n".join(errors))
                else:
                    st.success(
                        f"Done! {updated} updated, {skipped} skipped (date not found)."
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

        col_date.text(snap.snapshot_date.strftime("%b %Y"))
        col_assets.text(f"£{snap.total_assets:,.2f}" if snap.total_assets is not None else "-")
        col_liab.text(f"£{snap.total_liabilities:,.2f}" if snap.total_liabilities is not None else "-")
        col_nw.text(f"£{snap.net_worth:,.2f}" if snap.net_worth is not None else "-")
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
                        value=float(snap.total_assets) if snap.total_assets is not None else 0.0,
                        step=0.01,
                        format="%.2f",
                    )
                    no_liabilities = st.checkbox(
                        "No liabilities data",
                        value=snap.total_liabilities is None,
                    )
                    new_liabilities = None if no_liabilities else st.number_input(
                        "Total Liabilities",
                        value=float(snap.total_liabilities) if snap.total_liabilities is not None else 0.0,
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
                                    total_liabilities=Decimal(str(new_liabilities)) if new_liabilities is not None else None,
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
                            balance_gbp = Decimal(acct.get("balance_gbp") or acct["balance"])
                            currency = acct.get("currency", "GBP")
                            suffix = f" ({currency} {Decimal(acct['balance']):,.2f})" if currency != "GBP" else ""
                            name = acct.get("name") or acct.get("type_name", "Unknown")
                            st.text(f"  {name}: £{balance_gbp:,.2f}{suffix}")
                    if detail.get("liabilities"):
                        st.markdown("**Liabilities**")
                        for liab in detail["liabilities"]:
                            name = liab.get("name") or f"Type {liab.get('type_id', '?')}"
                            amount = Decimal(liab.get("amount") or liab.get("balance", "0"))
                            st.text(f"  {name}: £{amount:,.2f}")


def _latest_per_month(snapshots: list) -> list:
    """Return one snapshot per calendar month — the latest date in that month.

    Input is ascending by date; output is descending (most recent first).
    """
    seen: dict[tuple[int, int], object] = {}
    for snap in snapshots:
        key = (snap.snapshot_date.year, snap.snapshot_date.month)
        seen[key] = snap  # later dates overwrite earlier ones
    return list(reversed(list(seen.values())))


def _format_change(current: Decimal | None, previous: Decimal | None) -> str:
    """Format the change from previous snapshot."""
    if current is None or previous is None:
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
                str(snap.total_assets) if snap.total_assets is not None else "",
                str(snap.total_liabilities) if snap.total_liabilities is not None else "",
                str(snap.net_worth) if snap.net_worth is not None else "",
            ]
        )
    return output.getvalue()
