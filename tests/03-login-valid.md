---
id: 03-login-valid
title: Learner logs in with valid credentials
priority: high
timeout_seconds: 120
uat_id: AUTH-M-001
section: 4.1 User Authentication
---

## Setup
- Reset app state so the first screen appears:
  `adb shell pm clear com.example.bawana_revamp`
- App-specific pre-login gate: the app asks for a **site name** before showing
  the login form. Use `$SITE_NAME` env var (default for this project:
  `permata-revamp-stg`).
- Credentials are provided via env vars `$TEST_USER` and `$TEST_PASS`.
  DO NOT hardcode them into scenario files or step logs.
- Launch the app cold via `mobile_launch_app`.

## Steps
1. Launch the app
2. Wait up to 6 seconds for the "Enter site name" screen
3. Tap the site-name field and type `$SITE_NAME`, then tap "Next"
4. Wait up to 10 seconds for the login screen (UI tree contains username/email and password fields)
5. Dismiss any permission prompts or onboarding that appear
6. Tap the username/email field, type `$TEST_USER`
7. Tap the password field, type `$TEST_PASS`
8. Tap the primary "Login" / "Masuk" / "Sign in" button
9. Wait up to 15 seconds for the home/dashboard screen (new UI tree; login field no longer visible)

## Expected
- After step 7, UI tree no longer shows password field or "login" submit button
- UI tree contains at least one element indicating successful login (dashboard/home/profile/logout/welcome/menu)
- `logcat.filtered.txt` has no `FATAL EXCEPTION` entries for the app package
- Status = passed if all assertions hold; otherwise failed with short error message

## Notes
- Screenshot BEFORE typing password AND AFTER login success, but skip a screenshot immediately after typing if password field is visible-as-dots — still fine, masked is safe.
- If app requires OTP/2FA, this scenario can't handle it — record as failed with note.
