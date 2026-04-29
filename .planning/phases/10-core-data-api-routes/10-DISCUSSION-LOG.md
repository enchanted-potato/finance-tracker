# Phase 10: Core Data API Routes - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the discussion.

**Date:** 2026-04-29
**Phase:** 10-core-data-api-routes
**Mode:** discuss
**Areas discussed:** Entry history shape, Auto-snapshot on entry, Float vs string for money, Dashboard endpoint scope

## Discussion

### Entry history shape
**Question:** What should GET /api/accounts/history return?
**Options presented:**
- Grouped by date (array of day-objects with entries nested)
- Flat entries + separate daily-totals endpoints
- Single flat response, totals inlined as kind=total rows

**User selected:** Grouped by date
**Notes:** `entry_id` included in each entry so React delete/edit can target the record directly. Newest dates first. `total` server-computed.

---

### Auto-snapshot on balance write
**Question:** Should balance entry endpoints automatically call capture_snapshot()?
**Options presented:**
- Yes, auto-capture always
- Explicit /api/snapshots/capture endpoint
- Auto, but return snapshot in response

**User selected:** Yes, auto-capture always
**Notes:** Mirrors existing Streamlit behavior. Transparent to React client.

---

### Monetary values in JSON
**Question:** Should monetary values be JSON numbers or strings?
**Options presented:**
- JSON numbers (floats)
- Strings always
- Strings on write, floats on read

**User selected:** JSON numbers (floats)
**Notes:** Matches phase goal's "float schemas". Personal finance values well within float precision range. Recharts works natively.

---

### Dashboard endpoint scope
**Question:** Should Phase 10 include /api/dashboard?
**Options presented:**
- Include in Phase 10
- Defer to Phase 13

**User selected:** Include in Phase 10
**Notes:** API contract complete before React work starts. Phase 13 becomes pure React with no API work.

## Corrections Made

None — all recommendations accepted.

## Deferred Ideas

None.
