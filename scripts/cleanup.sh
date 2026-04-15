#!/bin/bash
# Stop any in-flight test orchestration safely:
#   - kills on-device screenrecord (mp4 finalizes)
#   - kills local adb logcat processes
#   - removes leftover /sdcard/current.mp4
#
# Usage: bash scripts/cleanup.sh
#
# Safe to run any time — exits 0 even if nothing was running.

set -u

ADB="${ADB:-/Users/netpolitan/Library/Android/sdk/platform-tools/adb}"
DEVICE="${DEVICE:-QSVKHASG6H5LMFKN}"

echo "→ stopping on-device screenrecord (if any)…"
"$ADB" -s "$DEVICE" shell 'pkill -INT screenrecord' 2>/dev/null || true
sleep 1

echo "→ removing leftover /sdcard/current.mp4…"
"$ADB" -s "$DEVICE" shell 'rm -f /sdcard/current.mp4' 2>/dev/null || true

echo "→ killing local adb logcat processes for this device…"
# Match adb logcat invocations targeting our DEVICE
PIDS=$(pgrep -f "adb -s $DEVICE logcat" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  echo "  killing PIDs: $PIDS"
  echo "$PIDS" | xargs -n1 kill 2>/dev/null || true
else
  echo "  none found"
fi

echo "→ cleaning .recordpid / .logcatpid marker files in runs/…"
find "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/runs" \
  \( -name '.recordpid' -o -name '.logcatpid' \) -type f -delete 2>/dev/null || true

echo "✓ cleanup done"
