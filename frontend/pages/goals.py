"""Goals page — track savings targets with progress and trend chart."""

from datetime import date
from decimal import Decimal, InvalidOperation

import plotly.graph_objects as go
import streamlit as st

from app.database import get_session
from app.models import Goal
from app.services.account_service import list_account_types
from app.services.goal_service import (
    compute_status,
    create_goal,
    delete_goal,
    get_current_value,
    list_goals,
    update_goal,
)
from app.services.snapshot_service import get_snapshot_history


def _get_user_id() -> str:
    return st.session_state["user_id"]


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

_STATUS_STYLE = {
    "Ahead": ("rgba(63,185,80,0.12)", "#3fb950"),
    "On Track": ("rgba(88,166,255,0.12)", "#58a6ff"),
    "Behind": ("rgba(248,81,73,0.12)", "#f85149"),
}

_PROGRESS_COLOR = {
    "Ahead": "linear-gradient(90deg,#14a760,#3fb950)",
    "On Track": "linear-gradient(90deg,#1f6feb,#58a6ff)",
    "Behind": "linear-gradient(90deg,#b91c1c,#f85149)",
}


def _fmt(amount: Decimal) -> str:
    return f"£{amount:,.0f}"


def _pct_color(pct: float, status: str) -> str:
    return _STATUS_STYLE[status][1]


def _summary_bar_html(total_saved: Decimal, total_target: Decimal) -> str:
    if total_target > 0:
        pct = min(float(total_saved / total_target * 100), 100.0)
    else:
        pct = 0.0
    remaining = max(total_target - total_saved, Decimal("0"))
    return f"""
<div style="background:rgba(31,111,235,0.08);border:1px solid rgba(88,166,255,0.2);
     border-radius:12px;padding:14px 20px;margin-bottom:20px;
     display:flex;align-items:center;gap:20px;">
  <div style="flex-shrink:0;">
    <div style="font-size:11px;color:#8b949e;font-weight:500;margin-bottom:3px;">TOTAL SAVED</div>
    <div style="font-size:22px;font-weight:700;color:#e6edf3;font-variant-numeric:tabular-nums;">{_fmt(total_saved)}</div>
  </div>
  <div style="flex:1;">
    <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
      <span style="font-size:11px;color:#8b949e;">Progress across all goals</span>
      <span style="font-size:12px;font-weight:600;color:#58a6ff;">{pct:.1f}% · {_fmt(remaining)} remaining</span>
    </div>
    <div style="background:#21262d;border-radius:100px;height:10px;overflow:hidden;">
      <div style="width:{pct:.1f}%;height:100%;border-radius:100px;
           background:linear-gradient(90deg,#1f6feb,#58a6ff);"></div>
    </div>
  </div>
  <div style="flex-shrink:0;text-align:right;">
    <div style="font-size:11px;color:#8b949e;font-weight:500;margin-bottom:3px;">TOTAL TARGET</div>
    <div style="font-size:22px;font-weight:700;color:#8b949e;font-variant-numeric:tabular-nums;">{_fmt(total_target)}</div>
  </div>
</div>
"""


def _goals_table_html(rows: list[dict]) -> str:
    if not rows:
        return ""

    header = """
<div style="background:#0d1117;border:1px solid #21262d;border-radius:14px;
     overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.25);">
<table style="width:100%;border-collapse:collapse;font-size:13px;">
  <thead>
    <tr>
      <th style="text-align:left;font-size:11px;font-weight:600;color:#8b949e;
          letter-spacing:0.5px;text-transform:uppercase;padding:10px 16px;
          border-bottom:1px solid #21262d;">Goal</th>
      <th style="text-align:left;font-size:11px;font-weight:600;color:#8b949e;
          letter-spacing:0.5px;text-transform:uppercase;padding:10px 16px;
          border-bottom:1px solid #21262d;">Current</th>
      <th style="text-align:left;font-size:11px;font-weight:600;color:#8b949e;
          letter-spacing:0.5px;text-transform:uppercase;padding:10px 16px;
          border-bottom:1px solid #21262d;">Target</th>
      <th style="text-align:left;font-size:11px;font-weight:600;color:#8b949e;
          letter-spacing:0.5px;text-transform:uppercase;padding:10px 16px;
          border-bottom:1px solid #21262d;">Progress</th>
      <th style="text-align:left;font-size:11px;font-weight:600;color:#8b949e;
          letter-spacing:0.5px;text-transform:uppercase;padding:10px 16px;
          border-bottom:1px solid #21262d;">Deadline</th>
      <th style="text-align:left;font-size:11px;font-weight:600;color:#8b949e;
          letter-spacing:0.5px;text-transform:uppercase;padding:10px 16px;
          border-bottom:1px solid #21262d;">Status</th>
    </tr>
  </thead>
  <tbody>
"""
    body = ""
    for i, r in enumerate(rows):
        border = "none" if i == len(rows) - 1 else "1px solid rgba(48,54,61,0.5)"
        status = r["status"]
        badge_bg, badge_color = _STATUS_STYLE[status]
        bar_color = _PROGRESS_COLOR[status]
        pct_color = badge_color
        pct = r["pct"]
        account_sub = (
            f'<div style="font-size:11px;color:#8b949e;margin-top:2px;">{r["account_name"]}</div>'
            if r["account_name"]
            else ""
        )
        body += f"""
    <tr style="border-bottom:{border};">
      <td style="padding:14px 16px;vertical-align:middle;">
        <div style="font-weight:600;color:#e6edf3;">{r["name"]}</div>
        {account_sub}
      </td>
      <td style="padding:14px 16px;vertical-align:middle;
          font-variant-numeric:tabular-nums;color:#e6edf3;">{_fmt(r["current"])}</td>
      <td style="padding:14px 16px;vertical-align:middle;
          font-variant-numeric:tabular-nums;color:#8b949e;">{_fmt(r["target"])}</td>
      <td style="padding:14px 16px;vertical-align:middle;min-width:140px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <div style="flex:1;background:#21262d;border-radius:100px;height:6px;overflow:hidden;">
            <div style="width:{min(pct, 100):.1f}%;height:100%;border-radius:100px;
                 background:{bar_color};"></div>
          </div>
          <span style="font-size:12px;font-weight:600;width:36px;text-align:right;
                flex-shrink:0;color:{pct_color};">{pct:.0f}%</span>
        </div>
      </td>
      <td style="padding:14px 16px;vertical-align:middle;color:#8b949e;font-size:12px;">
        {r["deadline"]}
      </td>
      <td style="padding:14px 16px;vertical-align:middle;">
        <span style="font-size:10px;font-weight:600;padding:3px 9px;border-radius:20px;
              text-transform:uppercase;letter-spacing:0.5px;
              background:{badge_bg};color:{badge_color};">{status}</span>
      </td>
    </tr>
"""
    footer = "  </tbody>\n</table>\n</div>"
    return header + body + footer


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

def _render_savings_chart(snapshots: list, total_target: Decimal) -> None:
    """Render Total Saved vs Total Targeted line chart using Plotly."""
    if not snapshots:
        st.info("No snapshot history yet — add account balances to see the trend.")
        return

    dates = [s.snapshot_date.date() for s in snapshots]
    saved_values = [
        float(s.total_assets) if s.total_assets is not None else None
        for s in snapshots
    ]
    target_val = float(total_target)

    fig = go.Figure()

    # Total Target — flat dashed line
    fig.add_trace(
        go.Scatter(
            x=[dates[0], dates[-1]],
            y=[target_val, target_val],
            mode="lines",
            name="Total Target",
            line={"color": "#f85149", "width": 2, "dash": "dash"},
        )
    )

    # Total Saved — filled area + line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=saved_values,
            mode="lines",
            name="Total Saved",
            line={"color": "#58a6ff", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
            connectgaps=True,
        )
    )

    fig.update_layout(
        xaxis=dict(gridcolor="#30363d", zerolinecolor="#30363d", color="#8b949e"),
        yaxis=dict(
            tickprefix="£",
            tickformat=",.0f",
            gridcolor="#30363d",
            zerolinecolor="#30363d",
            color="#8b949e",
        ),
        font=dict(color="#8b949e"),
        hovermode="x unified",
        margin={"l": 60, "r": 20, "t": 20, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render() -> None:
    """Render the Goals page."""
    user_id = _get_user_id()
    today = date.today()

    session = next(get_session())
    try:
        goals = list_goals(session=session, user_id=user_id)
        account_types = list_account_types(session=session, user_id=user_id)
        snapshots = get_snapshot_history(session=session, user_id=user_id)

        # Compute current value and status for each goal
        goal_rows: list[dict] = []
        for goal in goals:
            if goal.account_type_id is not None:
                current = get_current_value(
                    session=session,
                    user_id=user_id,
                    account_type_id=goal.account_type_id,
                )
            else:
                current = Decimal("0")
            status = compute_status(goal=goal, current_value=current, today=today)
            pct = float(current / goal.target_amount * 100) if goal.target_amount > 0 else 0.0
            at_name = next(
                (at.name for at in account_types if at.id == goal.account_type_id),
                None,
            )
            goal_rows.append(
                {
                    "id": goal.id,
                    "name": goal.name,
                    "account_name": at_name,
                    "account_type_id": goal.account_type_id,
                    "current": current,
                    "target": goal.target_amount,
                    "target_date": goal.target_date,
                    "deadline": goal.target_date.strftime("%b %Y"),
                    "pct": pct,
                    "status": status,
                }
            )
    finally:
        session.close()

    total_saved = sum((r["current"] for r in goal_rows), Decimal("0"))
    total_target = sum((r["target"] for r in goal_rows), Decimal("0"))

    # Page title
    st.markdown(
        '<div style="font-size:22px;font-weight:700;color:#e6edf3;margin-bottom:20px;">Goals</div>',
        unsafe_allow_html=True,
    )

    # Overall summary bar
    if goals:
        st.markdown(_summary_bar_html(total_saved, total_target), unsafe_allow_html=True)

    # Goals table
    if goal_rows:
        st.html(_goals_table_html(goal_rows))
    else:
        st.info("No goals yet. Use the Add / Edit Goal button below to get started.")

    # Chart
    st.markdown(
        '<div style="font-size:14px;font-weight:600;color:#e6edf3;margin-top:28px;margin-bottom:4px;">'
        "Total Saved vs Total Targeted</div>"
        '<div style="font-size:11px;color:#8b949e;margin-bottom:8px;">'
        "total assets over time vs combined goal targets</div>",
        unsafe_allow_html=True,
    )
    _render_savings_chart(snapshots, total_target)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # Add / Edit / Delete goals
    non_pension_types = [at for at in account_types if not at.is_pension]
    type_options = {at.name: at.id for at in non_pension_types}
    type_names = ["(none)"] + list(type_options.keys())

    if "show_manage_goal" not in st.session_state:
        st.session_state["show_manage_goal"] = False
    manage_label = "▲ Add / Edit Goal" if st.session_state["show_manage_goal"] else "▼ Add / Edit Goal"
    if st.button(manage_label, key="toggle_manage_goal"):
        st.session_state["show_manage_goal"] = not st.session_state["show_manage_goal"]
        st.rerun()

    if st.session_state["show_manage_goal"]:
        mode_options = ["Add", "Edit / Delete"] if goal_rows else ["Add"]
        mode = st.radio("", mode_options, horizontal=True, key="manage_goal_mode", label_visibility="collapsed")

        if mode == "Add":
            with st.form("add_goal_form", clear_on_submit=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                with c1:
                    new_name = st.text_input("Goal Name", placeholder="e.g. Emergency Fund")
                with c2:
                    new_account = st.selectbox("Linked Account", options=type_names)
                with c3:
                    new_target = st.number_input("Target Amount (£)", min_value=0.0, step=1000.0)
                with c4:
                    new_date = st.date_input("Target Date", value=date(today.year + 2, today.month, 1))
                submitted = st.form_submit_button("Add Goal", type="primary")
                if submitted:
                    if not new_name.strip():
                        st.error("Goal name is required.")
                    elif new_target <= 0:
                        st.error("Target amount must be greater than 0.")
                    else:
                        account_type_id = type_options.get(new_account) if new_account != "(none)" else None
                        session = next(get_session())
                        try:
                            create_goal(
                                session=session,
                                user_id=user_id,
                                name=new_name.strip(),
                                account_type_id=account_type_id,
                                target_amount=Decimal(str(new_target)),
                                target_date=new_date,
                            )
                        finally:
                            session.close()
                        st.success(f"Goal '{new_name.strip()}' added.")
                        st.rerun()

        else:
            goal_names = [r["name"] for r in goal_rows]
            selected_name = st.selectbox("Select goal", options=goal_names, key="edit_goal_select")
            selected_row = next(r for r in goal_rows if r["name"] == selected_name)

            with st.form("edit_goal_form"):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                with c1:
                    edit_name = st.text_input("Goal Name", value=selected_row["name"])
                with c2:
                    current_account = next(
                        (at.name for at in non_pension_types if at.id == selected_row["account_type_id"]),
                        "(none)",
                    )
                    edit_account = st.selectbox(
                        "Linked Account",
                        options=type_names,
                        index=type_names.index(current_account) if current_account in type_names else 0,
                    )
                with c3:
                    edit_target = st.number_input(
                        "Target Amount (£)",
                        min_value=0.0,
                        step=1000.0,
                        value=float(selected_row["target"]),
                    )
                with c4:
                    edit_date = st.date_input("Target Date", value=selected_row["target_date"])

                col_save, col_delete = st.columns([1, 1])
                with col_save:
                    save_clicked = st.form_submit_button("Save Changes", type="primary")
                with col_delete:
                    delete_clicked = st.form_submit_button("Delete Goal")

                if save_clicked:
                    if not edit_name.strip():
                        st.error("Goal name is required.")
                    elif edit_target <= 0:
                        st.error("Target amount must be greater than 0.")
                    else:
                        account_type_id = type_options.get(edit_account) if edit_account != "(none)" else None
                        session = next(get_session())
                        try:
                            update_goal(
                                session=session,
                                goal_id=selected_row["id"],
                                user_id=user_id,
                                name=edit_name.strip(),
                                account_type_id=account_type_id,
                                target_amount=Decimal(str(edit_target)),
                                target_date=edit_date,
                            )
                        finally:
                            session.close()
                        st.success("Goal updated.")
                        st.rerun()

                if delete_clicked:
                    session = next(get_session())
                    try:
                        delete_goal(
                            session=session,
                            goal_id=selected_row["id"],
                            user_id=user_id,
                        )
                    finally:
                        session.close()
                    st.success(f"Goal '{selected_row['name']}' deleted.")
                    st.rerun()
