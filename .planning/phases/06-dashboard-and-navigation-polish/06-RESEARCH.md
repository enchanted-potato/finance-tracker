# Phase 6: Dashboard and Navigation Polish - Research

**Researched:** 2026-03-07
**Domain:** Streamlit CSS injection, Plotly axis formatting, custom HTML metric cards
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Metric cards (DASH-01, DASH-02)**
- Custom HTML/CSS cards via `st.markdown(unsafe_allow_html=True)` — established pattern in main.py
- Replace `st.metric()` with custom HTML div cards
- Soft pastel background (10-15% opacity of category color), no border, rounded corners
- Subtle drop shadow (`box-shadow: 0 4px 12px rgba(0,0,0,0.08)`)
- Colors by metric: Net Worth=blue, Assets=green, Liabilities=red, Pension=neutral/grey
- Negative Net Worth delta shown in red; positive delta shown in green (DASH-02 fix)
- Current delta bug: `_net_worth_delta` returns `£-1234.56` — the `£` prefix before `-` causes Streamlit metric to treat negative as positive. Fix by moving the sign handling correctly in the custom HTML cards.

**Line chart y-axis (DASH-03)**
- Fix: use `tickprefix="£"` and `tickformat=",.0f"` separately — the current `yaxis_tickformat="£,.0f"` is not valid d3-format
- Result: y-axis labels like "£1,250" with comma separators

**Pension bar chart (DASH-04 + layout change)**
- Change chart type: single stacked bar showing total pension height, with each pension provider as a stacked segment
- X-axis: single "Pension" category; each provider is a stacked bar trace
- Bars should be narrower — set `width` parameter on `go.Bar` to control bar width
- CSS drop shadow on all Plotly chart containers (not per-bar) — `box-shadow: 0 4px 12px rgba(0,0,0,0.08)` applied to `.stPlotlyChart` elements
- Shadow applies to all dashboard charts for visual consistency

**Sidebar active indicator (NAV-01)**
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-01 | Metric cards display as styled rounded boxes with soft colored backgrounds (Net Worth=blue, Assets=green, Liabilities=red) | Custom HTML/CSS via `st.markdown(unsafe_allow_html=True)` in dashboard.py; replace four `st.metric()` calls |
| DASH-02 | Net Worth delta is shown in red when negative (not green) | `_net_worth_delta()` returns raw Decimal delta; custom HTML card conditionally applies red/green color class based on sign |
| DASH-03 | Line chart y-axis displays values with thousands comma separator | Replace invalid `yaxis_tickformat="£,.0f"` with `yaxis=dict(tickprefix="£", tickformat=",.0f")` — confirmed independent Plotly parameters |
| DASH-04 | Pension bar chart has drop shadows for visual depth | CSS targeting `.stPlotlyChart` container div; Plotly charts have transparent backgrounds so shadow must go on the container, not SVG |
| NAV-01 | Sidebar active page indicator uses a color other than orange | Change active button from `type="primary"` to `type="secondary"`; inject CSS left-border rule targeting `button[kind="primary"]` (or a data-key class) for active state |
</phase_requirements>

---

## Summary

This phase is pure frontend — no backend changes, no new dependencies, no database touches. All five requirements are addressed through two files: `frontend/pages/dashboard.py` (DASH-01 through DASH-04) and `frontend/main.py` (NAV-01 + shared CSS injection).

The core technical challenge is that Streamlit intentionally limits styling, so all visual customization goes through `st.markdown(unsafe_allow_html=True)` CSS injection, which is already established in `main.py`. The metric card replacement (DASH-01/02) is the largest change: four `st.metric()` calls become custom HTML divs rendered with `st.markdown`. The Plotly y-axis fix (DASH-03) is a one-line correction. The pension chart restructure (DASH-04) is a moderate rewrite of `_render_pension_bar()`. The sidebar change (NAV-01) swaps `type="primary"` for `type="secondary"` on all nav buttons and adds a CSS left-border rule for the active state via a data-key class selector.

**Primary recommendation:** Execute changes in order — CSS/sidebar first (NAV-01), then metric cards (DASH-01/02), then chart fixes (DASH-03/DASH-04). Each change is self-contained within its function/block.

## Standard Stack

### Core (already installed — no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Streamlit | current | Page rendering, CSS injection via `st.markdown` | Project's UI framework |
| Plotly (plotly.graph_objects) | current | Chart rendering | Already used for all charts |
| Python HTML strings | n/a | Custom metric card markup | `st.markdown(unsafe_allow_html=True)` is the established pattern |

No new packages required. All changes use libraries already present.

**Installation:** None needed.

## Architecture Patterns

### File Boundaries
```
frontend/
├── main.py          # CSS injection block (~line 162), sidebar nav loop (~line 269)
└── pages/
    └── dashboard.py # Metric cards (~line 48), _render_line_chart (~line 121),
                     # _render_pension_bar (~line 254), _net_worth_delta (~line 98)
```

### Pattern 1: CSS Injection at App Startup
**What:** All global CSS goes into the `st.markdown(...)` block in `main.py` — it runs once per session on every page load. This is where chart shadow and sidebar border CSS lives.
**When to use:** Any CSS that must apply globally (across pages or affecting sidebar elements).
**Example:**
```python
# In main.py inside the existing st.markdown block
"""
/* Drop shadow on all Plotly chart containers */
.stPlotlyChart {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    border-radius: 8px;
}

/* Active sidebar button: left border accent only */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: transparent !important;
    color: #141413 !important;
    font-weight: 500 !important;
    border-left: 3px solid #141413 !important;
    padding-left: 13px !important;  /* compensate for border width */
}
"""
```

### Pattern 2: Custom HTML Metric Cards
**What:** Replace `st.metric()` with `st.markdown(html, unsafe_allow_html=True)` inside each column. HTML div contains label, value, and conditional delta styling.
**When to use:** When `st.metric()` does not support the required styling (background color, rounded box, conditional delta color).
**Example:**
```python
# Source: established pattern in main.py CSS injection
delta_val = current_net_worth - previous_net_worth  # Decimal arithmetic
delta_color = "red" if delta_val < 0 else "green"
delta_str = f"£{delta_val:+,.2f}"  # +/- prefix via format spec

html = f"""
<div style="
    background: rgba(33, 24, 231, 0.10);
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
">
    <div style="font-size: 13px; color: #555; font-weight: 500;">Net Worth</div>
    <div style="font-size: 28px; font-weight: 700; color: #141413;">£{net_worth:,.2f}</div>
    <div style="font-size: 13px; color: {delta_color}; font-weight: 500;">{delta_str}</div>
</div>
"""
st.markdown(html, unsafe_allow_html=True)
```

### Pattern 3: Plotly Axis Prefix + Format (Separate Parameters)
**What:** Use `tickprefix` and `tickformat` as distinct axis parameters — they are independent and compose correctly.
**When to use:** Any Plotly chart needing a currency symbol (prefix) plus thousands formatting.
**Example:**
```python
# Fix for _render_line_chart and _render_pension_bar
# WRONG (invalid d3 format — £ is not a d3 format specifier):
fig.update_layout(yaxis_tickformat="£,.0f")

# CORRECT (separate independent parameters):
fig.update_layout(
    yaxis=dict(
        tickprefix="£",
        tickformat=",.0f",
    )
)
```

### Pattern 4: Stacked Bar Chart with go.Bar traces
**What:** One `go.Bar` trace per pension provider, all sharing `x=["Pension"]`. Set `barmode="stack"` on the layout.
**When to use:** Replacing the current multi-bar flat chart with a single stacked column.
**Example:**
```python
fig = go.Figure()
colors = ["#A855F7", "#7C3AED", "#6D28D9", "#5B21B6"]  # purple scale
for i, account in enumerate(pension_accounts):
    fig.add_trace(go.Bar(
        name=account.name,
        x=["Pension"],
        y=[float(account.balance)],
        marker_color=colors[i % len(colors)],
        width=0.3,  # narrower than default ~0.8
    ))
fig.update_layout(
    barmode="stack",
    yaxis=dict(tickprefix="£", tickformat=",.0f"),
    showlegend=True,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin={"l": 60, "r": 20, "t": 20, "b": 40},
)
```

### Pattern 5: Sidebar Active State via CSS Attribute Selector
**What:** Streamlit renders `type="primary"` as `kind="primary"` attribute on the `<button>` HTML element. This is a real DOM attribute, targetable with CSS `[kind="primary"]`.
**When to use:** Styling the active nav button differently from inactive buttons without custom HTML.
**Key insight:** The existing `main.py` CSS already uses `.stButton > button[kind="primary"]` — this confirms the selector works. The change is to modify what styles that selector applies (remove orange background, add left border).

### Anti-Patterns to Avoid
- **Modifying `yaxis_tickformat` with `£` prefix in the format string:** `"£,.0f"` is not valid d3-format. The `£` will be silently ignored or cause unexpected output.
- **Applying box-shadow directly to Plotly SVG elements:** Plotly charts have transparent backgrounds (`paper_bgcolor="rgba(0,0,0,0)"`). The shadow must target the `.stPlotlyChart` container div, not the SVG.
- **Keeping `type="primary"` on active button:** If you only add CSS for the left border without changing `type`, the orange background CSS (which has `!important`) overrides the border styling. The fix requires changing `type="secondary"` for ALL nav buttons and targeting active via a different mechanism.
- **Putting delta sign in the formatted string before detecting sign:** The current `_net_worth_delta` returns `"£-1234.56"` — the `£` before `-` makes string-based sign detection fail. Compute delta as `Decimal` first, check sign, then format.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thousands formatting | Custom Python formatting in chart label | `tickformat=",.0f"` in Plotly layout | Plotly handles axis label rendering; d3-format covers all edge cases |
| Active nav indicator | JavaScript-based active detection | CSS `[kind="primary"]` attribute selector | Streamlit already sets the `kind` attribute on the rendered button |
| Per-card conditional color | Inline style computation in a loop | f-string color variable in HTML template | Simple conditional — no abstraction needed |

## Common Pitfalls

### Pitfall 1: Invalid d3 Format String with Currency Symbol
**What goes wrong:** `yaxis_tickformat="£,.0f"` silently fails — `£` is not a d3-format specifier and the format may render without thousands separator or produce unexpected output.
**Why it happens:** d3-format strings have a specific mini-language; arbitrary prefix characters are not part of it. The current code has this bug in both `_render_line_chart` and `_render_pension_bar`.
**How to avoid:** Always use `tickprefix` for the currency symbol and `tickformat` for the numeric format separately.
**Warning signs:** y-axis shows values without comma separators, or shows `£` in unexpected positions.

### Pitfall 2: Orange Background Overriding Left Border on Active Button
**What goes wrong:** Adding a `border-left` to `.stButton > button[kind="primary"]` while keeping `background-color: #d97757 !important` means the orange background remains — the border is invisible against it.
**Why it happens:** The existing `!important` on `background-color` for `kind="primary"` in `main.py` takes precedence.
**How to avoid:** Change all nav buttons to `type="secondary"`, then add a NEW CSS rule targeting the active button by a different mechanism (e.g., scoped key class `.stkey_nav_Dashboard` or session state–driven inline style).
**Warning signs:** Active button still shows orange after the CSS change.

**Active state mechanism options (Claude's discretion area):**
- Option A: Session state + inline style in Python — generate the `border-left` as inline style in the button's containing div via `st.markdown` before `st.sidebar.button`. Avoids CSS specificity issues entirely.
- Option B: CSS key class selector — Streamlit adds `.stkey_nav_{page}` class to each button's container. Active page button can be targeted with `[data-testid="stSidebar"] .stkey_nav_Dashboard button`. Requires knowing which page is active at CSS-injection time (not possible — CSS is static).
- Option C: Wrap active button in a custom HTML div with border styling and render a disabled-looking button inside. Fragile.
- **Recommended:** Option A (inline style or wrapping `st.markdown` around the active button). The `kind="primary"` approach is cleaner only if the orange is fully removed.

### Pitfall 3: Pension Bar Width on Single-Item X-Axis
**What goes wrong:** A stacked bar with a single x-category defaults to very wide bars (filling the plot width). `width` parameter on `go.Bar` is in x-axis data units — for categorical axes, 1.0 = full category width. A value of 0.3 gives 30% of the category slot.
**Why it happens:** Plotly auto-scales single-category bars to fill available space.
**How to avoid:** Set `width=0.3` (or similar) on each `go.Bar` trace. All traces in a stack must use the same `width` value.
**Warning signs:** Bar spans the entire chart width regardless of data.

### Pitfall 4: Metric Card Delta — Sign Detection
**What goes wrong:** If `_net_worth_delta` returns a formatted string `"£-1234.56"` and you try `if delta_str.startswith("-")` — this fails because the string starts with `£`.
**Why it happens:** The current function formats the string with `£` prefix before the sign. The CONTEXT.md documents this as the root cause of the existing `st.metric` bug.
**How to avoid:** In the new implementation, keep `delta` as a `Decimal` value, check `delta < 0` for color, then format. Do not use the existing `_net_worth_delta()` string return — either modify it to return `Decimal` or inline the logic in the card rendering.

## Code Examples

Verified patterns from source code and official docs:

### Existing CSS Injection Block (main.py ~line 162)
The `st.markdown` block in `main.py` is the single place for all global CSS. New rules for chart shadows and sidebar border go here, inside the existing `<style>` tag.

### Sidebar Button Loop (main.py ~line 269)
```python
for page, icon in pages.items():
    is_active = st.session_state["selected_page"] == page
    if st.sidebar.button(
        f"{icon}  {page}",
        key=f"nav_{page}",
        use_container_width=True,
        type="primary" if is_active else "secondary",  # <-- change ALL to "secondary"
    ):
```
After change: all buttons render as `kind="secondary"`. Active state indicated by left border CSS on the container or inline.

### Plotly Stacked Bar Layout
```python
# barmode must be set on layout, not per trace
fig.update_layout(barmode="stack")
```

### CSS Selector Confirmed Working in This Codebase
```css
/* Already in main.py — confirms kind attribute is real DOM attribute */
.stButton > button[kind="primary"] {
    background-color: #d97757 !important;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `st.metric()` for KPI cards | Custom HTML div via `st.markdown` | Phase 6 | Full control over background, border-radius, delta color |
| `yaxis_tickformat="£,.0f"` | `yaxis=dict(tickprefix="£", tickformat=",.0f")` | Phase 6 | Valid d3-format, correct thousands separator |
| Flat multi-bar pension chart | Single stacked bar per provider | Phase 6 | Cleaner visual, shows composition |
| Orange `kind="primary"` active nav | Left border accent, `type="secondary"` | Phase 6 | Less visually dominant, matches design intent |

## Open Questions

1. **Sidebar active border — CSS specificity vs. inline style approach**
   - What we know: `button[kind="primary"]` works as a CSS selector (confirmed by existing code). Changing all buttons to `type="secondary"` means the active button no longer has a CSS hook.
   - What's unclear: The cleanest way to mark the active button without relying on `type`. Key-class selectors (`.stkey_nav_Dashboard`) could work but require verifying Streamlit adds that class reliably.
   - Recommendation: Use inline style on a wrapping `st.markdown` div before the active button, or verify `.stkey_nav_{page}` class is present in the rendered DOM and use that as the CSS hook. Either is fine — planner should pick one and document it.

2. **Pension bar `width` unit on categorical axis**
   - What we know: Plotly `go.Bar` `width` is in x-axis data units. For categorical axes, the behavior is implementation-dependent.
   - What's unclear: Whether `width=0.3` on a categorical axis gives 30% of slot width or behaves differently.
   - Recommendation: Start with `width=0.3` and adjust empirically. The bar will be visually inspected — this is a discretion item.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (configured in pyproject.toml) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | Metric cards render as styled HTML (visual) | manual-only | n/a — Streamlit rendering, no testable Python logic | n/a |
| DASH-02 | Negative delta color is red | unit | `pytest tests/test_dashboard_helpers.py::test_net_worth_delta_negative -x` | ❌ Wave 0 |
| DASH-03 | Line chart y-axis uses tickprefix + tickformat | unit | `pytest tests/test_dashboard_helpers.py::test_line_chart_tick_format -x` | ❌ Wave 0 |
| DASH-04 | Pension chart container has shadow (CSS, visual) | manual-only | n/a — CSS injection, no Python logic to unit test | n/a |
| NAV-01 | Active nav button type change | manual-only | n/a — Streamlit widget type attribute, no testable logic | n/a |

**Note on manual-only items:** DASH-01, DASH-04, and NAV-01 are pure visual/CSS changes. The correct verification is visual inspection in the running app. No unit test can validate rendered CSS or Streamlit widget appearance.

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_dashboard_helpers.py` — covers DASH-02 (delta sign logic) and DASH-03 (chart axis config)
  - DASH-02 test: verify that when delta is negative, the rendered HTML string contains `color: red` (or equivalent)
  - DASH-03 test: verify `_render_line_chart` Plotly figure has `tickprefix="£"` and `tickformat=",.0f"` set
  - Both tests operate on pure Python logic/return values — no Streamlit or DB dependency

## Sources

### Primary (HIGH confidence)
- `frontend/pages/dashboard.py` — read directly; all function signatures, current bugs, line numbers confirmed
- `frontend/main.py` — read directly; CSS injection block, sidebar loop, `kind="primary"` selector confirmed active in codebase
- `tests/conftest.py`, `pyproject.toml` — read directly; pytest configuration confirmed

### Secondary (MEDIUM confidence)
- [Plotly Tick Formatting — official docs](https://plotly.com/python/tick-formatting/) — confirms `tickformat` uses d3 mini-language; `tickprefix` and `tickformat` are independent parameters
- [Plotly yaxis reference](https://plotly.com/python/reference/layout/yaxis/) — confirms `tickprefix` adds text before tick labels; separate from `tickformat`
- WebSearch result citing Streamlit forum — confirms `kind="primary"` renders as DOM attribute on `<button>` element, targetable with CSS `button[kind="primary"]`

### Tertiary (LOW confidence)
- None — all critical claims verified against source code or official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — confirmed from source files; no new dependencies
- Architecture: HIGH — patterns verified from existing `main.py` and `dashboard.py` code
- Pitfalls: HIGH — bugs confirmed from reading actual source (invalid d3 format, sign detection issue documented in CONTEXT.md)
- Validation: MEDIUM — test gap identification is accurate; wave 0 test content is estimated

**Research date:** 2026-03-07
**Valid until:** 2026-09-07 (stable domain — Streamlit CSS injection and Plotly axis formatting APIs are stable)
