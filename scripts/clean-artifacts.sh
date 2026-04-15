#!/bin/bash
# Wipe all test artifacts + stop any lingering processes so the next batch
# starts from a clean slate.
#
# Effects:
#   - stops on-device screenrecord (so mp4 finalizes properly)
#   - removes /sdcard/current.mp4 from the device
#   - kills local `adb logcat` processes for this device
#   - removes runs/* entirely (videos, screenshots, logs, reports, symlinks)
#
# Usage:  bash scripts/clean-artifacts.sh [--keep-latest]
#
#   --keep-latest   preserve the newest run directory (useful when re-running
#                   but wanting to compare against the last report)

set -u

ADB="${ADB:-/Users/netpolitan/Library/Android/sdk/platform-tools/adb}"
DEVICE="${DEVICE:-QSVKHASG6H5LMFKN}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNS_DIR="$PROJECT_ROOT/runs"

KEEP_LATEST=0
if [ "${1:-}" = "--keep-latest" ]; then
  KEEP_LATEST=1
fi

echo "→ stopping on-device screenrecord (if any)…"
"$ADB" -s "$DEVICE" shell 'pkill -INT screenrecord' 2>/dev/null || true
sleep 1

echo "→ removing leftover /sdcard/current.mp4…"
"$ADB" -s "$DEVICE" shell 'rm -f /sdcard/current.mp4' 2>/dev/null || true

echo "→ killing local adb logcat processes for this device…"
PIDS=$(pgrep -f "adb -s $DEVICE logcat" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  echo "  killing PIDs: $PIDS"
  echo "$PIDS" | xargs -n1 kill 2>/dev/null || true
  sleep 0.5
  # hard-kill any that survived
  STILL=$(pgrep -f "adb -s $DEVICE logcat" 2>/dev/null || true)
  [ -n "$STILL" ] && echo "$STILL" | xargs -n1 kill -9 2>/dev/null || true
else
  echo "  none found"
fi

if [ -d "$RUNS_DIR" ]; then
  if [ "$KEEP_LATEST" = "1" ]; then
    LATEST=$(ls -td "$RUNS_DIR"/*/ 2>/dev/null | head -1 || true)
    if [ -n "$LATEST" ]; then
      echo "→ removing all runs EXCEPT $(basename "$LATEST")…"
      find "$RUNS_DIR" -mindepth 1 -maxdepth 1 ! -path "${LATEST%/}" -exec rm -rf {} +
    else
      echo "→ runs/ is empty, nothing to keep"
    fi
  else
    echo "→ wiping $RUNS_DIR/* …"
    # keep the directory itself but remove all contents (including latest.log symlink)
    find "$RUNS_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  fi
else
  echo "→ runs/ does not exist, creating it"
  mkdir -p "$RUNS_DIR"
fi

echo "→ clearing any lingering .recordpid / .logcatpid markers…"
find "$RUNS_DIR" \( -name '.recordpid' -o -name '.logcatpid' \) -type f -delete 2>/dev/null || true

echo "✓ clean-artifacts done"
