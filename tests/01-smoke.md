---
id: 01-smoke
title: App launches without crash
priority: high
timeout_seconds: 60
---

## Setup
- APK already installed fresh (handled by prepare-run.sh + `adb install -r -g`)
- Device in portrait orientation

## Steps
1. Launch app via its package name (use `mobile_launch_app`)
2. Wait up to 10 seconds for the main UI (UI tree contains at least one clickable/focusable element)
3. Read UI tree once to confirm presence of elements; capture a screenshot

## Expected
- App process is the foreground activity for the target package (check via
  `adb shell dumpsys activity activities | grep mResumedActivity`)
- `logcat.filtered.txt` contains no lines matching `FATAL EXCEPTION` or `ANR in`
- No "has stopped" / ANR system dialog appears on screen
