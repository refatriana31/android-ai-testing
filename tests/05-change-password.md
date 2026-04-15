---
id: 05-change-password
title: Learner changes password from Account Settings (with self-revert)
priority: high
timeout_seconds: 240
---

## Setup
- Reset app state: `adb shell pm clear com.example.bawana_revamp`
- Site name via `$SITE_NAME` (default: `permata-revamp-stg`)
- Current password via `$TEST_PASS`; username via `$TEST_USER`
- Temporary new password (generated locally for this test):
  `IisTest_2026Aa`
- Self-revert: at the end the test changes the password BACK to `$TEST_PASS`
  so the account is left in the original state.

## Steps
1. Launch the app (after `pm clear`)
2. Wait for site-name screen, type `$SITE_NAME`, tap Next
3. Wait for login screen, type `$TEST_USER` and `$TEST_PASS`, tap Login
4. Handle post-login onboarding (e.g. language selection: pick English + Confirm)
5. Wait for home/dashboard
6. Navigate to Account Settings (look for: profile tab/icon, side menu, settings gear)
7. Find and tap "Change Password" / "Ubah Kata Sandi" option
8. Enter the current password (`$TEST_PASS`) in the "Current/Old Password" field
9. Enter the new password (`IisTest_2026Aa`) in the "New Password" field
10. Enter the new password again in the "Confirm Password" field (if such field exists)
11. Tap the Save / Submit / Update button
12. Verify success indicator (toast, snackbar, dialog, or navigation away from form)
13. **Revert phase**: navigate back to Change Password (re-login if app logged us out)
14. Enter `IisTest_2026Aa` as current; enter `$TEST_PASS` as new (and confirm)
15. Tap Save; verify success again
16. Final state: account password is back to `$TEST_PASS`

## Expected
- Step 12: success indicator visible (any of: "success", "berhasil", "saved",
  "tersimpan", "updated", "diperbarui"; or navigation back to settings)
- Step 15: same, confirming the revert worked
- No FATAL EXCEPTION in `logcat.filtered.txt`
- If step 12 succeeds but step 15 fails: status = `failed` AND error must
  state clearly that the password is currently `IisTest_2026Aa` so the user
  can recover.

## Notes
- App may auto-logout after a password change. If so, step 13 includes a
  re-login using the NEW password (`IisTest_2026Aa`).
- If the app shows a confirmation dialog after Save, accept it.
- If "Change Password" is not under "Account Settings" but elsewhere
  (e.g., "Security", "Profile"), follow the actual UI tree and record the
  navigation path in the step `note` field.
