---
id: 02-navigation
title: Basic navigation works (forward + back button)
priority: medium
timeout_seconds: 90
---

## Setup
- APK installed fresh
- App cold-launched to its main screen

## Steps
1. Launch app via its package name
2. Wait for the main screen to become interactive (UI tree has ≥1 clickable, non-system element)
3. Snapshot the current UI tree (remember the list of element texts — call this `main_screen`)
4. Tap the first NON-system clickable element (exclude status bar, nav bar buttons)
5. Wait 1 second; snapshot the UI tree again — it must differ from `main_screen`
6. Press the hardware BACK button (`mobile_press_button` with `"BACK"`)
7. Wait 1 second; snapshot UI tree — it should match `main_screen` again

## Expected
- Step 5: new UI tree is meaningfully different (element texts changed)
- Step 7: UI tree matches the `main_screen` snapshot from Step 3
- No crashes in `logcat.filtered.txt` during the whole flow

## Notes
- If the first clickable element is a dialog/permission prompt, dismiss it first
  and re-snapshot `main_screen` before starting the navigation flow. Record this
  in the step `note` field.
