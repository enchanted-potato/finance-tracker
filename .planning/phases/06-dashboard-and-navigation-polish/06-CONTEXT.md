# Phase 6: Dashboard and Navigation Polish - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Cosmetic and visual improvements to the dashboard metric cards, line/bar charts, and sidebar navigation — no new data models, no backend changes. Pure frontend (dashboard.py and main.py). Phase ends when all five requirements (DASH-01 through DASH-04, NAV-01) are satisfied.

</domain>

<decisions>
## Implementation Decisions

### Metric cards (DASH-01, DASH-02)
- Custom HTML/CSS cards via `st.markdown(unsafe_allow_html=True)` — established pattern in main.py
- Replace `st.metric()` with custom HTML div cards
- Soft pastel background (10-15% opacity of category color), no border, rounded corners
- Subtle drop shadow (e.g. `box-shadow: 0 4px 12px rgba(0,0,0,0.08)`)
- Colors by metric: Net Worth=blue, Assets=green, Liabilities=red, Pension=neutral/grey
- Negative Net Worth delta shown in red; positive delta shown in green (DASH-02 fix)
- Current delta bug: `_net_worth_delta` returns `£-1234.56` — the `£` prefix before `-` causes Streamlit metric to treat negative as positive. Fix by moving the sign handling correctly in the custom HTML cards.

### Line chart y-axis (DASH-03)
- Fix: use `tickprefix="£"` and `tickformat=",.0f"` separately — the current `yaxis_tickformat="£,.0f"` is not valid d3-format
- Result: y-axis labels like "£1,250" with comma separators

### Pension bar chart (DASH-04 + layout change)
- Change chart type: single stacked bar showing total pension height, with each pension provider as a stacked segment
- X-axis: single "Pension" category; each provider is a stacked bar trace
- Bars should be narrower (current width is too wide) — set `width` parameter on `go.Bar` to control bar width
- CSS drop shadow on all Plotly chart containers (not per-bar) — subtle, `box-shadow: 0 4px 12px rgba(0,0,0,0.08)` applied to `.stPlotlyChart` elements
- Shadow applies to all dashboard charts for visual consistency

### Sidebar active indicator (NAV-01)
- Remove the orange `kind="primary"` background fill from the active button
- Active page: left border accent (3-4px dark/near-black border, e.g. `#141413`) — no background color change
- Inactive pages: no border, same as current hover behavior
- Sidebar background: leave as default Streamlit grey (no change)
- Logout button: leave as-is (no change)

### Claude's Discretion
- Exact shade of pastel backgrounds for each card color (blue, green, red, grey)
- Exact border radius and padding on the metric cards
- Exact bar width value for the pension stacked chart
- Mechanism for applying left border accent to sidebar buttons (CSS targeting or custom HTML)

</decisions>

<specifics>
## Specific Ideas

- Pension chart: user specifically wants bars thinner than the current default — set `width` on `go.Bar` traces
- Pension chart: single stacked bar (one column) with providers as segments + legend, not multiple side-by-side bars
- Sidebar: "no color for the selected state" — emphasis is through the left border only, not background fill or text color change

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `st.markdown(..., unsafe_allow_html=True)` in `main.py`: already used for CSS injection — same approach for metric card HTML and chart shadow CSS
- `_render_pension_bar()` in `dashboard.py:201`: current flat bar chart — replace with stacked `go.Bar` traces per provider
- `_render_line_chart()` in `dashboard.py:107`: fix `yaxis_tickformat` → split into `tickprefix` + `tickformat`
- `_net_worth_delta()` in `dashboard.py:173`: returns formatted string — delta sign detection must change with custom HTML cards

### Established Patterns
- Custom CSS injected in `main.py` at startup: add chart shadow CSS and sidebar active border CSS here
- Plotly figures use `paper_bgcolor="rgba(0,0,0,0)"` and `plot_bgcolor="rgba(0,0,0,0)"`: transparent backgrounds — CSS drop shadow targets the container div, not the SVG
- Sidebar buttons use `type="primary"` for active state in `main.py:224` — change to `type="secondary"` for all and apply CSS border instead

### Integration Points
- `frontend/pages/dashboard.py` — metric cards and all chart rendering
- `frontend/main.py` — sidebar CSS injection block (~line 175) and sidebar button loop (~line 215)
- Active state CSS must target `[data-testid="stSidebar"] .stButton > button[kind="primary"]` or equivalent selector

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-dashboard-and-navigation-polish*
*Context gathered: 2026-03-07*
