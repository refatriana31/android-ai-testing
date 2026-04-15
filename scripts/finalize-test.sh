#!/bin/bash
# Stop video + logcat for a single test, pull mp4, filter logcat by package.
#
# Usage:  finalize-test.sh <test-dir> <status>
#   status = "passed" | "failed" | "error"  (informational only; written into steps.json later by Claude)

set -euo pipefail

ADB="${ADB:-/Users/netpolitan/Library/Android/sdk/platform-tools/adb}"
DEVICE="${DEVICE:-QSVKHASG6H5LMFKN}"

TEST_DIR="${1:?usage: finalize-test.sh <test-dir> <status>}"
STATUS="${2:-unknown}"

if [ ! -d "$TEST_DIR" ]; then
  echo "ERROR: test dir not found: $TEST_DIR" >&2
  exit 2
fi

# Gracefully stop on-device screenrecord so mp4 header finalizes
"$ADB" -s "$DEVICE" shell pkill -INT screenrecord 2>/dev/null || true
sleep 2

# Pull video (best-effort — may be missing if test was very short)
if "$ADB" -s "$DEVICE" shell 'test -f /sdcard/current.mp4' 2>/dev/null; then
  "$ADB" -s "$DEVICE" pull /sdcard/current.mp4 "$TEST_DIR/video.mp4" >/dev/null 2>&1 || true
  "$ADB" -s "$DEVICE" shell rm -f /sdcard/current.mp4 2>/dev/null || true
fi

# Stop logcat capture
if [ -f "$TEST_DIR/.logcatpid" ]; then
  LPID=$(cat "$TEST_DIR/.logcatpid")
  kill "$LPID" 2>/dev/null || true
  wait "$LPID" 2>/dev/null || true
  rm -f "$TEST_DIR/.logcatpid"
fi

# Filter logcat: keep only lines relevant to the app package + crashes + ANRs
RUN_DIR="$(dirname "$TEST_DIR")"
PKG=""
if [ -f "$RUN_DIR/meta.json" ]; then
  PKG=$(grep -o '"package":[[:space:]]*"[^"]*"' "$RUN_DIR/meta.json" \
    | head -1 | sed -E 's/.*"([^"]+)"$/\1/' || true)
fi

if [ -f "$TEST_DIR/logcat.raw.txt" ]; then
  if [ -n "$PKG" ]; then
    grep -E "$PKG|AndroidRuntime|ActivityManager.*(ANR|FATAL|died)|FATAL EXCEPTION|ANR in " \
      "$TEST_DIR/logcat.raw.txt" > "$TEST_DIR/logcat.filtered.txt" || true
  else
    grep -E "AndroidRuntime|FATAL EXCEPTION|ANR in " \
      "$TEST_DIR/logcat.raw.txt" > "$TEST_DIR/logcat.filtered.txt" || true
  fi
fi

VIDEO_EXISTS="false"
if [ -f "$TEST_DIR/video.mp4" ]; then VIDEO_EXISTS="true"; fi

cat <<EOF
{
  "test_dir": "$TEST_DIR",
  "status": "$STATUS",
  "ended_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "video_captured": $VIDEO_EXISTS,
  "logcat_filtered": "$TEST_DIR/logcat.filtered.txt"
}
EOF
