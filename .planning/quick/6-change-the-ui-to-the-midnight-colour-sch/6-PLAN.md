---
phase: quick-6
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - .streamlit/config.toml
  - frontend/main.py
  - frontend/pages/dashboard.py
  - frontend/pages/history.py
  - frontend/pages/accounts.py
  - frontend/pages/liabilities.py
  - frontend/pages/pension.py
autonomous: true
requirements: [QUICK-6]

must_haves:
  truths:
    - "App background is dark (#161b22), not the warm paper colour (#faf9f5)"
    - "Sidebar active nav item shows a blue left border (#58a6ff) with blue text"
    - "All Plotly charts render on a transparent/dark background with dark grid lines"
    - "Metric cards use the Midnight text colour (#e6edf3) for values and (#8b949e) for labels"
    - "History table badges, dividers and cell colours use Midnight palette values"
  artifacts:
    - path: ".streamlit/config.toml"
      provides: "Streamlit theme tokens (primaryColor, backgroundColor, secondaryBackgroundColor, textColor)"
      contains: "#161b22"
    - path: "frontend/main.py"
      provides: "Global CSS block with app background and sidebar nav styling"
      contains: "#58a6ff"
    - path: "frontend/pages/dashboard.py"
      provides: "Metric card HTML and Plotly chart layout"
      contains: "#e6edf3"
    - path: "frontend/pages/history.py"
      provides: "History table CSS and inline colour strings"
      contains: "#8b949e"
  key_links:
    - from: ".streamlit/config.toml"
      to: "Streamlit theme"
      via: "[theme] section"
      pattern: "primaryColor.*#58a6ff"
    - from: "frontend/main.py"
      to: ".stApp background"
      via: "CSS .stApp rule"
      pattern: "background-color.*#161b22"
---

<objective>
Apply the Midnight colour scheme to the entire Streamlit app, replacing all warm paper-tone colours with the dark GitHub-style Midnight palette.

Purpose: Make the app feel like a polished dark-mode finance tool instead of the current warm beige/paper theme.
Output: Every hardcoded colour across config, global CSS, pages, and Plotly charts updated to Midnight equivalents.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Midnight palette (authoritative reference for this plan):
  App bg:             #161b22
  Sidebar bg:         #0d1117
  Card/secondary bg:  #21262d
  Border:             #30363d
  Primary accent:     #58a6ff
  Text primary:       #e6edf3
  Text secondary:     #8b949e
  Positive (green):   #3fb950
  Negative (red):     #f85149
  Hover bg:           rgba(255,255,255,0.05)
  Active nav bg:      rgba(88,166,255,0.1)
  Chart grid/zero:    #30363d
  Chart font:         #8b949e
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update config.toml and global CSS (main.py)</name>
  <files>.streamlit/config.toml, frontend/main.py</files>
  <action>
Update `.streamlit/config.toml` — replace the entire [theme] block:
```toml
[theme]
primaryColor = "#58a6ff"
backgroundColor = "#161b22"
secondaryBackgroundColor = "#21262d"
textColor = "#e6edf3"
font = "sans serif"
```

Update `frontend/main.py` — in the `st.markdown("""<style>...""")` block inside `main()`:

1. Replace `.stApp` background:
   - `#faf9f5` → `#161b22`

2. Replace nav button default text colour:
   - `color: #141413 !important;` (in `.stButton > button`) → `color: #e6edf3 !important;`

3. Replace nav button hover background:
   - `background-color: #e8e6dc !important;` (in `.stButton > button:hover`) → `background-color: rgba(255,255,255,0.05) !important;`

4. Replace nav button active background:
   - `background-color: #b0aea5 !important;` (in `.stButton > button:active`) → `background-color: #30363d !important;`

5. Replace active sidebar nav (primary button) styles — the `[data-testid="stSidebar"] .stButton > button[kind="primary"]` rule:
   - `color: #141413 !important;` → `color: #58a6ff !important;`
   - `border-left: 3px solid #141413 !important;` → `border-left: 3px solid #58a6ff !important;`
   - Keep `background-color: transparent !important;` and `padding-left: 13px !important;` unchanged
   - Add after: `background-color: rgba(88,166,255,0.1) !important;`

6. Replace active nav hover:
   - `background-color: #e8e6dc !important;` (in the `[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover` rule) → `background-color: rgba(88,166,255,0.15) !important;`

7. Update Plotly chart shadow to suit dark theme:
   - `box-shadow: 0 4px 12px rgba(0,0,0,0.08);` → `box-shadow: 0 4px 12px rgba(0,0,0,0.4);`
  </action>
  <verify>
    <automated>python -c "
import re
cfg = open('.streamlit/config.toml').read()
assert '#161b22' in cfg, 'config.toml missing bg'
assert '#58a6ff' in cfg, 'config.toml missing primary'
assert '#e6edf3' in cfg, 'config.toml missing textColor'
main = open('frontend/main.py').read()
assert '#161b22' in main, 'main.py missing app bg'
assert '#58a6ff' in main, 'main.py missing accent'
assert '#faf9f5' not in main, 'main.py still has warm bg'
assert '#141413' not in main, 'main.py still has warm text'
assert '#e8e6dc' not in main, 'main.py still has hover colour'
assert '#b0aea5' not in main, 'main.py still has active colour'
print('PASS')
"
    </automated>
  </verify>
  <done>config.toml uses Midnight theme tokens; main.py CSS uses Midnight nav and background colours; no warm-paper colours remain in either file.</done>
</task>

<task type="auto">
  <name>Task 2: Update dashboard.py metric cards and Plotly chart colours</name>
  <files>frontend/pages/dashboard.py</files>
  <action>
In `frontend/pages/dashboard.py`, update all hardcoded colours:

1. `_build_net_worth_card_html()` — update inline styles:
   - `color: #555;` → `color: #8b949e;`
   - `color: #141413;` (value text) → `color: #e6edf3;`
   - `color: red` / `color: green` in delta line → keep as-is (these are semantic) but replace with Midnight semantic: `color: #f85149` for red and `color: #3fb950` for green
     - Change: `delta_color = "red" if delta < 0 else "green"` → `delta_color = "#f85149" if delta < 0 else "#3fb950"`

2. Total Assets card (col2 `st.markdown`):
   - `color: #555;` → `color: #8b949e;`
   - `color: #141413;` → `color: #e6edf3;`

3. Total Liabilities card (col3 `st.markdown`):
   - `color: #555;` → `color: #8b949e;`
   - `color: #141413;` → `color: #e6edf3;`

4. Total Pension card (col4 `st.markdown`):
   - `color: #555;` → `color: #8b949e;`
   - `color: #141413;` → `color: #e6edf3;`

5. `_render_line_chart()` — add Midnight chart styling to `fig.update_layout(...)`:
   - Add `font=dict(color="#8b949e")` to layout
   - Add `xaxis=dict(gridcolor="#30363d", zerolinecolor="#30363d", color="#8b949e")`
   - Add `yaxis` update to include `gridcolor="#30363d", zerolinecolor="#30363d", color="#8b949e"` alongside existing tickprefix/tickformat (merge into the existing yaxis dict)

6. `_render_asset_pie()` and `_render_liability_pie()` — add to `fig.update_layout(...)`:
   - Add `font=dict(color="#8b949e")`

7. `_render_pension_bar()` — add to `fig.update_layout(...)`:
   - Add `font=dict(color="#8b949e")`
   - Add `xaxis=dict(gridcolor="#30363d", zerolinecolor="#30363d")`
   - Merge into existing yaxis dict: `gridcolor="#30363d", zerolinecolor="#30363d", color="#8b949e"`
  </action>
  <verify>
    <automated>python -c "
src = open('frontend/pages/dashboard.py').read()
assert '#e6edf3' in src, 'missing primary text colour'
assert '#8b949e' in src, 'missing secondary text colour'
assert '#f85149' in src, 'missing negative colour'
assert '#3fb950' in src, 'missing positive colour'
assert '#30363d' in src, 'missing grid colour'
assert 'color: #141413' not in src, 'still has warm text'
assert 'color: #555' not in src, 'still has warm label colour'
print('PASS')
"
    </automated>
  </verify>
  <done>All metric cards use Midnight text/label colours; all Plotly charts have dark grid lines and font colour; delta colours use semantic Midnight palette.</done>
</task>

<task type="auto">
  <name>Task 3: Update history.py, accounts.py, liabilities.py, and pension.py</name>
  <files>frontend/pages/history.py, frontend/pages/accounts.py, frontend/pages/liabilities.py, frontend/pages/pension.py</files>
  <action>
**history.py** — update `_inject_styles()` CSS block and inline strings:

CSS class colour replacements (all inside the `<style>` block):
- `.hist-th` color: `rgba(20,20,19,0.4)` → `#8b949e`
- `.hist-header` border-bottom: `rgba(20,20,19,0.12)` → `rgba(230,237,243,0.12)`
- `.year-label` color: `#a07830` → `#58a6ff`
- `.year-line` background: `rgba(20,20,19,0.1)` → `rgba(230,237,243,0.1)`
- `.cell-date` color: `rgba(20,20,19,0.55)` → `#8b949e`
- `.cell-money` color: `rgba(20,20,19,0.8)` → `#e6edf3`
- `.cell-nw` color: `rgba(20,20,19,0.95)` → `#e6edf3`
- `.badge-pos` color: `#1e8c57` → `#3fb950`; background: `rgba(30,140,87,0.1)` → `rgba(63,185,80,0.12)`
- `.badge-neg` color: `#c0392b` → `#f85149`; background: `rgba(192,57,43,0.08)` → `rgba(248,81,73,0.12)`
- `.badge-neu` color: `rgba(20,20,19,0.35)` → `rgba(230,237,243,0.35)`; background: `rgba(20,20,19,0.05)` → `rgba(230,237,243,0.05)`
- `.row-sep` border-top: `rgba(20,20,19,0.07)` → `rgba(230,237,243,0.07)`
- `.detail-wrap` background: `rgba(20,20,19,0.04)` → `rgba(230,237,243,0.04)`
- `.detail-title` color: `rgba(20,20,19,0.4)` → `#8b949e`
- `.detail-row` border-bottom: `rgba(20,20,19,0.06)` → `rgba(230,237,243,0.06)`
- `.detail-name` color: `rgba(20,20,19,0.5)` → `#8b949e`
- `.detail-val` color: `rgba(20,20,19,0.85)` → `#e6edf3`
- `.detail-suffix` color: `rgba(20,20,19,0.35)` → `rgba(230,237,243,0.35)`

Inline string in `_edit_modal()`:
- `color:#a07830` → `color:#58a6ff`

**accounts.py** — update the metric card `st.markdown` HTML:
- `color: #555;` → `color: #8b949e;`
- `color: #141413;` → `color: #e6edf3;`

**liabilities.py** — update the metric card `st.markdown` HTML:
- `color: #555;` → `color: #8b949e;`
- `color: #141413;` → `color: #e6edf3;`

**pension.py** — update the metric card `st.markdown` HTML:
- `color: #555;` → `color: #8b949e;`
- `color: #141413;` → `color: #e6edf3;`
  </action>
  <verify>
    <automated>python -c "
import re

for path, checks in [
    ('frontend/pages/history.py', ['#58a6ff', '#3fb950', '#f85149', '#8b949e', '#e6edf3']),
    ('frontend/pages/accounts.py', ['#8b949e', '#e6edf3']),
    ('frontend/pages/liabilities.py', ['#8b949e', '#e6edf3']),
    ('frontend/pages/pension.py', ['#8b949e', '#e6edf3']),
]:
    src = open(path).read()
    for colour in checks:
        assert colour in src, f'{path} missing {colour}'
    for bad in ['#a07830', 'color: #141413', 'color: #555', '#1e8c57', '#c0392b']:
        assert bad not in src, f'{path} still contains old colour {bad}'

print('PASS')
"
    </automated>
  </verify>
  <done>All four pages use Midnight text/label colours; history badges use semantic Midnight colours; no warm-paper colours remain in any page file.</done>
</task>

</tasks>

<verification>
After all three tasks complete, run a final sweep to confirm no warm-paper colours remain anywhere in the frontend:

```bash
python -c "
import os, re, sys
warm = ['#faf9f5', '#d6d4c5', '#141413', '#e8e6dc', '#b0aea5', '#a07830', 'color: #555', '1e8c57', 'c0392b']
files = [
    '.streamlit/config.toml',
    'frontend/main.py',
    'frontend/pages/dashboard.py',
    'frontend/pages/history.py',
    'frontend/pages/accounts.py',
    'frontend/pages/liabilities.py',
    'frontend/pages/pension.py',
]
found = []
for f in files:
    src = open(f).read()
    for w in warm:
        if w in src:
            found.append(f'{f}: {w}')
if found:
    print('FAIL — warm colours still present:')
    for x in found: print(' ', x)
    sys.exit(1)
print('PASS — all warm colours replaced')
"
```
</verification>

<success_criteria>
- `.streamlit/config.toml` theme block uses all four Midnight tokens
- `frontend/main.py` app background is #161b22, sidebar active nav is blue (#58a6ff)
- All metric cards across dashboard, accounts, liabilities, and pension pages show text in #e6edf3 (values) and #8b949e (labels)
- Plotly charts in dashboard use dark grid lines (#30363d) and font colour #8b949e
- History table uses Midnight badge colours: positive #3fb950, negative #f85149
- History year dividers are blue (#58a6ff) instead of amber (#a07830)
- No warm-paper hex values (#faf9f5, #d6d4c5, #141413, #e8e6dc, #b0aea5, #a07830) remain in any frontend file
</success_criteria>

<output>
After completion, create `.planning/quick/6-change-the-ui-to-the-midnight-colour-sch/6-SUMMARY.md`
</output>
