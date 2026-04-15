---
id: 04-login-invalid
title: Invalid password shows a clear error on mobile
priority: high
timeout_seconds: 90
uat_id: AUTH-M-002
section: 4.1 User Authentication
---

## Setup
- Reset app state so the first screen appears:
  `adb shell pm clear com.example.bawana_revamp`
- Site name via `$SITE_NAME` (default: `permata-revamp-stg`).
- Valid username from `$TEST_USER`; intentionally bad password: `WrongPass_XYZ_invalid!` (generated locally — NOT from `$TEST_PASS`).
- Launch the app cold via `mobile_launch_app`.

## Steps
1. Launch the app
2. Wait up to 6 seconds for the "Enter site name" screen
3. Tap the site-name field and type `$SITE_NAME`, then tap "Next"
4. Wait up to 10 seconds for the login screen (UI tree contains username/email and password fields)
5. Dismiss any permission prompts/onboarding (only if they appear)
6. Tap username/email field, type `$TEST_USER`
7. Tap password field, type the bad password `WrongPass_XYZ_invalid!`
8. Tap the primary "Login" / "Masuk" / "Sign in" button
9. Wait up to 8 seconds for any error indicator

## Expected
- UI tree continues to show the login form (still on login screen — not navigated away)
- UI tree contains an error element. Acceptable markers (case-insensitive, any of):
  - English: "invalid", "incorrect", "wrong", "error", "failed", "please try again"
  - Indonesian: "salah", "tidak valid", "gagal", "tidak cocok", "coba lagi"
  - Or a snackbar/toast/dialog surfaced in the UI tree
- No app crash: `logcat.filtered.txt` has no `FATAL EXCEPTION` entries
- Status = passed if error is surfaced AND user stays on login screen; otherwise failed.

## Notes
- Clear error visibility is the goal — a silent failure (nothing happens on tap) = failed.
- If the app doesn't react at all after 8 seconds (no error, no navigation), that's a failure with note "no error feedback shown".
