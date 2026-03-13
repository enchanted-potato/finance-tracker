---
phase: quick-6
plan: 1
subsystem: frontend
tags: [ui, theme, colours, dark-mode, plotly]
key-decisions:
  - "Replaced warm paper theme wholesale across all 7 frontend files — config.toml, main.py, dashboard, history, accounts, liabilities, pension"
  - "Active sidebar nav background set to rgba(88,166,255,0.1) alongside existing border-left approach — keeps the CSS hook"
  - "Delta colours in _build_net_worth_card_html changed from 'red'/'green' string literals to #f85149/#3fb950 Midnight semantic values"
key-files:
  modified:
    - .streamlit/config.toml
    - frontend/main.py
    - frontend/pages/dashboard.py
    - frontend/pages/history.py
    - frontend/pages/accounts.py
    - frontend/pages/liabilities.py
    - frontend/pages/pension.py
metrics:
  completed: "2026-03-13"
---

# Quick Task 6: Midnight Colour Scheme Summary

**One-liner:** Dark GitHub-style Midnight palette applied across all Streamlit pages, replacing warm beige/paper theme with #161b22 background, #58a6ff accents, and #e6edf3/#8b949e text.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Update config.toml and global CSS (main.py) | 52b57a9 | .streamlit/config.toml, frontend/main.py |
| 2 | Update dashboard.py metric cards and Plotly chart colours | 07bc3e0 | frontend/pages/dashboard.py |
| 3 | Update history.py, accounts.py, liabilities.py, pension.py | 3ea417a | frontend/pages/history.py, accounts.py, liabilities.py, pension.py |

## What Was Done

**Task 1 — config.toml and main.py:**
- `.streamlit/config.toml` [theme] block replaced: primaryColor `#58a6ff`, backgroundColor `#161b22`, secondaryBackgroundColor `#21262d`, textColor `#e6edf3`
- `.stApp` background changed from `#faf9f5` to `#161b22`
- Nav button default colour: `#141413` -> `#e6edf3`
- Nav button hover: `#e8e6dc` -> `rgba(255,255,255,0.05)`
- Nav button active: `#b0aea5` -> `#30363d`
- Active sidebar nav: text and border-left changed to `#58a6ff`; background added as `rgba(88,166,255,0.1)`
- Active nav hover: `#e8e6dc` -> `rgba(88,166,255,0.15)`
- Chart container shadow opacity increased from 0.08 to 0.4 for dark theme

**Task 2 — dashboard.py:**
- All metric card label colours: `#555` -> `#8b949e`
- All metric card value colours: `#141413` -> `#e6edf3`
- Delta colour literals (`"red"/"green"`) -> Midnight semantic (`#f85149`/`#3fb950`)
- Line chart: added `font`, `xaxis`, merged `yaxis` with `gridcolor="#30363d"`, `zerolinecolor="#30363d"`, `color="#8b949e"`
- Asset and liability pie charts: added `font=dict(color="#8b949e")`
- Pension bar chart: added `font`, `xaxis`, merged `yaxis` Midnight grid colours

**Task 3 — remaining pages:**
- history.py: all `rgba(20,20,19,...)` CSS values replaced with `rgba(230,237,243,...)` equivalents
- history.py: `.year-label` colour `#a07830` -> `#58a6ff`
- history.py: `.badge-pos` -> `#3fb950` / `rgba(63,185,80,0.12)`, `.badge-neg` -> `#f85149` / `rgba(248,81,73,0.12)`
- history.py edit modal inline colour: `#a07830` -> `#58a6ff`
- accounts.py, liabilities.py, pension.py: metric card label/value updated to `#8b949e`/`#e6edf3`

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `.streamlit/config.toml` contains `#161b22`, `#58a6ff`, `#e6edf3` ✓
- `frontend/main.py` contains `#161b22`, `#58a6ff`; free of `#faf9f5`, `#141413`, `#e8e6dc`, `#b0aea5` ✓
- `frontend/pages/dashboard.py` contains `#e6edf3`, `#8b949e`, `#f85149`, `#3fb950`, `#30363d` ✓
- All four remaining pages contain `#8b949e`, `#e6edf3`; free of old warm colours ✓
- Final sweep: PASS — all warm colours replaced ✓
