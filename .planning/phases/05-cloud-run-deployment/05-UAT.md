---
status: complete
phase: 05-cloud-run-deployment
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md]
started: 2026-03-05T00:00:00Z
updated: 2026-03-05T00:01:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Open a fresh browser tab (private/incognito). Navigate to https://finance-tracker-rntookejza-uc.a.run.app. The Cloud Run service should boot (may take a few seconds on cold start) and serve the app. No error page, no "Service Unavailable", no crash. The Streamlit app loads and shows a UI (login or dashboard).
result: pass

### 2. Login Screen Displays
expected: The app shows a login screen with a "Sign in with Google" button (or equivalent Firebase auth UI). No dashboard content is visible before authentication. The page is clean and functional.
result: pass

### 3. Google Sign-In Authentication
expected: Clicking "Sign in with Google" opens a Google OAuth popup or redirect. Completing auth with your Google account returns you to the app, now authenticated. No errors like "invalid credential" or Firebase errors in the UI.
result: pass

### 4. Dashboard Loads After Login
expected: After successful login, the main net worth dashboard appears. The page shows your accounts/liabilities section (even if empty). No 500 errors, no blank white screen, no "test-user" errors.
result: pass

### 5. Add an Account
expected: Find the UI to add an account (e.g., bank account, investment). Fill in name and value, submit. The new account appears in the accounts list with the correct name and value.
result: pass

### 6. Add a Liability
expected: Find the UI to add a liability (e.g., credit card, loan). Fill in name and value, submit. The new liability appears in the liabilities list with the correct name and value.
result: pass

### 7. Data Persists After Refresh
expected: Hard-refresh the page (Cmd+Shift+R or F5). The accounts and liabilities you added in the previous tests are still there — data survived the page reload because it's stored in Cloud SQL.
result: pass

### 8. Net Worth Snapshot
expected: Find the option to take/save a snapshot of current net worth. After triggering it, the net worth total (assets minus liabilities) is calculated and displayed or saved. No errors.
result: pass

### 9. Logout
expected: Find and click the logout button/link. After logout, you are returned to the login screen. The dashboard content is no longer visible. Attempting to visit the app URL again shows the login screen (not the dashboard).
result: pass

## Summary

total: 9
passed: 9
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
