#!/bin/bash
# Prepare a single test: create dirs, capture device+APK info (once per run),
# start screen recording and logcat in background. Prints JSON with paths.
#
# Usage:  prepare-run.sh <test-id> [run-dir]
#
# Env overrides:
#   ADB     path to adb (default: Android SDK platform-tools)
#   AAPT    path to aapt (default: Android SDK build-tools/37.0.0)
#   DEVICE  adb device serial (default: QSVKHASG6H5LMFKN)
#   APK     path to APK file (default: ./app-release.apk, relative to project root)

set -euo pipefail

ADB="${ADB:-/Users/netpolitan/Library/Android/sdk/platform-tools/adb}"
AAPT="${AAPT:-/Users/netpolitan/Library/Android/sdk/build-tools/37.0.0/aapt}"
DEVICE="${DEVICE:-QSVKHASG6H5LMFKN}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APK="${APK:-$PROJECT_ROOT/app-release.apk}"

TEST_ID="${1:?usage: prepare-run.sh <test-id> [run-dir]}"
RUN_DIR="${2:-}"

if [ -z "$RUN_DIR" ]; then
  TS=$(date +%Y-%m-%d_%H-%M-%S)
  RUN_DIR="$PROJECT_ROOT/runs/$TS"
fi

TEST_DIR="$RUN_DIR/test-$TEST_ID"
mkdir -p "$TEST_DIR"

# Maintain a stable `runs/latest.log` → current run's progress.log
# so the user can `tail -F runs/latest.log` from another terminal.
RUNS_ROOT="$(dirname "$RUN_DIR")"
PROGRESS_LOG="$RUN_DIR/progress.log"
touch "$PROGRESS_LOG"
# replace the latest.log symlink (best-effort; fall back to copy if symlinks fail)
ln -sfn "$PROGRESS_LOG" "$RUNS_ROOT/latest.log" 2>/dev/null || true

log_progress() {
  printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" >> "$PROGRESS_LOG"
}

log_progress "prepare-run test-id=$TEST_ID"

# Device reachability check
if ! "$ADB" -s "$DEVICE" shell echo ok >/dev/null 2>&1; then
  echo "ERROR: device $DEVICE not reachable via adb" >&2
  exit 2
fi

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().rstrip()))' 2>/dev/null \
    || printf '"%s"' "$(printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')"
}

# Create meta.json once per run
if [ ! -f "$RUN_DIR/meta.json" ]; then
  MODEL=$("$ADB" -s "$DEVICE" shell getprop ro.product.model | tr -d '\r\n')
  BRAND=$("$ADB" -s "$DEVICE" shell getprop ro.product.brand | tr -d '\r\n')
  OS_VER=$("$ADB" -s "$DEVICE" shell getprop ro.build.version.release | tr -d '\r\n')
  SDK=$("$ADB" -s "$DEVICE" shell getprop ro.build.version.sdk | tr -d '\r\n')
  BUILD_ID=$("$ADB" -s "$DEVICE" shell getprop ro.build.display.id | tr -d '\r\n')
  SCREEN_SIZE=$("$ADB" -s "$DEVICE" shell wm size | head -1 | awk -F': ' '{print $2}' | tr -d '\r\n')
  DENSITY=$("$ADB" -s "$DEVICE" shell wm density | head -1 | awk -F': ' '{print $2}' | tr -d '\r\n')

  PKG=""; VER_NAME=""; VER_CODE=""; APK_SIZE=0
  if [ -f "$APK" ] && [ -x "$AAPT" ]; then
    APK_SIZE=$(stat -f%z "$APK" 2>/dev/null || stat -c%s "$APK" 2>/dev/null || echo 0)
    APK_INFO=$("$AAPT" dump badging "$APK" 2>/dev/null || true)
    PKG_LINE=$(printf '%s\n' "$APK_INFO" | grep -m1 '^package:')
    PKG=$(printf '%s' "$PKG_LINE"      | sed -E "s/^package: name='([^']+)'.*/\\1/" || true)
    VER_NAME=$(printf '%s' "$PKG_LINE" | sed -E "s/.*[[:space:]]versionName='([^']+)'.*/\\1/" || true)
    VER_CODE=$(printf '%s' "$PKG_LINE" | sed -E "s/.*[[:space:]]versionCode='([^']+)'.*/\\1/" || true)
  fi

  cat > "$RUN_DIR/meta.json" <<EOF
{
  "run_id": "$(basename "$RUN_DIR")",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "device": {
    "serial": "$DEVICE",
    "brand": "$BRAND",
    "model": "$MODEL",
    "android_version": "$OS_VER",
    "sdk": "$SDK",
    "build": "$BUILD_ID",
    "screen_size": "$SCREEN_SIZE",
    "density": "$DENSITY"
  },
  "apk": {
    "path": "$APK",
    "package": "$PKG",
    "version_name": "$VER_NAME",
    "version_code": "$VER_CODE",
    "size_bytes": $APK_SIZE
  }
}
EOF
fi

# Clear any stray on-device screenrecord and the previous mp4
"$ADB" -s "$DEVICE" shell 'pkill -INT screenrecord; rm -f /sdcard/current.mp4' 2>/dev/null || true
sleep 0.3

# Start screen recording detached ON THE DEVICE (adb shell returns immediately).
# We stop it later via `pkill -INT screenrecord` which makes the mp4 finalize.
"$ADB" -s "$DEVICE" shell \
  'nohup screenrecord --time-limit 180 /sdcard/current.mp4 </dev/null >/dev/null 2>&1 &'

# Start logcat capture locally (clear first, then follow into a file)
"$ADB" -s "$DEVICE" logcat -c 2>/dev/null || true
nohup "$ADB" -s "$DEVICE" logcat -v time > "$TEST_DIR/logcat.raw.txt" 2>/dev/null &
LOGCAT_PID=$!
echo $LOGCAT_PID > "$TEST_DIR/.logcatpid"

log_progress "prepared test-dir=$TEST_DIR logcat_pid=$LOGCAT_PID"

cat <<EOF
{
  "run_dir": "$RUN_DIR",
  "test_dir": "$TEST_DIR",
  "test_id": "$TEST_ID",
  "logcat_pid": $LOGCAT_PID,
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
