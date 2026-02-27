---
phase: 05-cloud-run-deployment
plan: 04
subsystem: database
tags: [sqlmodel, schema, single-user, firebase-auth]

# Dependency graph
requires:
  - phase: 05-02
    provides: GCP infrastructure setup with Cloud SQL instance
provides:
  - Simplified single-user schema without users table
  - Firebase UID stored directly in user_id fields
  - Validation blocking 'test-user' in production
affects: [05-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [single-user-schema, direct-uid-storage, firebase-primary-key]

key-files:
  created: []
  modified: [app/models.py, app/services/auth_service.py, frontend/main.py]

key-decisions:
  - "Remove users table entirely — single-user app doesn't need user records table"
  - "Store Firebase UID directly as string in user_id fields with no FK constraints"
  - "Block 'test-user' as valid user_id in application validation"
  - "No data migration needed — Cloud SQL database is empty, fresh start"

patterns-established:
  - "Direct Firebase UID storage: user_id fields are plain strings (max_length=128) with no foreign keys"
  - "Application-level validation: Block test user IDs in auth_service.get_or_create_user()"

requirements-completed: [DEPLOY-05]

# Metrics
duration: 87min
completed: 2026-02-27
---

# Phase 05 Plan 04: Schema Simplification Summary

**Single-user schema with users table removed, Firebase UID stored directly in all models, and test-user validation blocking production usage**

## Performance

- **Duration:** 87 min (1h 27m)
- **Started:** 2026-02-27T16:34:29Z
- **Completed:** 2026-02-27T18:01:28Z
- **Tasks:** 10 (9 code changes + 1 verification)
- **Files modified:** 3

## Accomplishments
- Removed User model from app/models.py completely
- Removed 6 foreign key constraints from user_id fields across 5 models (AccountType, Account, LiabilityType, Liability, Snapshot)
- Simplified auth_service.get_or_create_user() to validate and return Firebase UID string
- Added validation to block 'test-user' as valid user_id in production
- Updated frontend code to handle string UID return value
- Schema ready for fresh Cloud SQL deployment with no migration needed

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove User model from app/models.py** - `5cd3289` (refactor)
2. **Task 2: Remove FK constraint from AccountType.user_id** - `b19e560` (refactor)
3. **Task 3: Remove FK constraint from Account.user_id** - `8d6bbaf` (refactor)
4. **Task 4: Remove FK constraint from LiabilityType.user_id** - `6146275` (refactor)
5. **Task 5: Remove FK constraint from Liability.user_id** - `ba17f3c` (refactor)
6. **Task 6: Remove FK constraint from Snapshot.user_id** - `8f166c7` (refactor)
7. **Task 7: Remove User model import from auth_service.py** - `1becb2d` (refactor)
8. **Task 8: Simplify get_or_create_user function** - `deedb42` (refactor)
9. **Task 9: Update frontend code to use UID string** - `e6477b9` (refactor)
10. **Task 10: Verify schema changes are correct** - (checkpoint approval, no code changes)

## Files Created/Modified
- `app/models.py` - Removed User model, removed FK constraints from 6 user_id fields
- `app/services/auth_service.py` - Removed User import, simplified get_or_create_user to validate and return UID string with test-user blocking
- `frontend/main.py` - Updated to handle string UID return from get_or_create_user

## Decisions Made

**1. Remove users table entirely**
- Single-user app doesn't need a users table to track multiple users
- Firebase UID serves as the user identifier throughout the application
- Simplifies schema and eliminates unnecessary table

**2. Store Firebase UID directly as string in user_id fields**
- No foreign key constraints to users table
- user_id fields remain as `Field(max_length=128)` plain strings
- Direct storage eliminates join overhead and simplifies queries

**3. Block 'test-user' as valid user_id in validation**
- Application-level validation in auth_service.get_or_create_user()
- Raises ValueError if uid == 'test-user'
- Prevents test data from polluting production database

**4. No data migration needed**
- Cloud SQL database is empty (fresh start)
- No existing user records to migrate
- Clean deployment with simplified schema from day one

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all schema changes completed without errors. Verification checkpoint confirmed:
- User model removed completely
- All FK constraints to users.id removed
- user_id fields remain as plain strings
- test-user validation active
- Frontend updated to handle string return
- No remaining User model references in codebase

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Cloud Run deployment (Plan 05-03):**
- Simplified schema ready for fresh Cloud SQL database
- No migration scripts needed (database is empty)
- Application code updated to work with string UIDs
- Test user blocked from production usage
- All models use direct Firebase UID storage

**Blockers/Concerns:**
- None - schema simplification complete and verified

## Self-Check: PASSED

All files verified:
- FOUND: app/models.py
- FOUND: app/services/auth_service.py
- FOUND: frontend/main.py

All commits verified:
- FOUND: 5cd3289 (Task 1)
- FOUND: b19e560 (Task 2)
- FOUND: 8d6bbaf (Task 3)
- FOUND: 6146275 (Task 4)
- FOUND: ba17f3c (Task 5)
- FOUND: 8f166c7 (Task 6)
- FOUND: 1becb2d (Task 7)
- FOUND: deedb42 (Task 8)
- FOUND: e6477b9 (Task 9)

---
*Phase: 05-cloud-run-deployment*
*Completed: 2026-02-27*
