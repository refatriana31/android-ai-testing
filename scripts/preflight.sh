#!/bin/bash
# Pre-flight check for a batch test run. Verifies that the testing infra is
# ready before we invest ~1-2h of device time.
#
# Does NOT verify credentials (app-level login is driven by Claude via MCP in
# a separate sanity step — see CLAUDE.md "Credential sanity" recipe).
#
# Exits non-zero if any check fails. Prints a readable summary either way.
#
# Usage:  bash scripts/preflight.sh

set -u

ADB="${ADB:-/Users/netpolitan/Library/Android/sdk/platform-tools/adb}"
AAPT="${AAPT:-/Users/netpolitan/Library/Android/sdk/build-tools/37.0.0/aapt}"
DEVICE="${DEVICE:-QSVKHASG6H5LMFKN}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APK="${APK:-$PROJECT_ROOT/app-release.apk}"

FAIL=0
note() { printf "  %s\n" "$*"; }
pass() { printf "  \033[32mOK\033[0m  %s\n" "$*"; }
fail() { printf "  \033[31mFAIL\033[0m %s\n" "$*"; FAIL=1; }
warn() { printf "  \033[33mWARN\033[0m %s\n" "$*"; }

echo "→ checking adb binary…"
if [ ! -x "$ADB" ]; then
  fail "adb not executable at $ADB"
else
  pass "adb: $("$ADB" version | head -1)"
fi

echo "→ checking aapt binary…"
if [ ! -x "$AAPT" ]; then
  warn "aapt not executable at $AAPT (APK metadata will be blank)"
else
  pass "aapt present"
fi

echo "→ checking APK…"
if [ ! -f "$APK" ]; then
  fail "APK not found at $APK"
else
  SIZE=$(stat -f%z "$APK" 2>/dev/null || stat -c%s "$APK" 2>/dev/null || echo 0)
  pass "APK: $APK ($(( SIZE / 1024 / 1024 )) MB)"
  if [ -x "$AAPT" ]; then
    PKG=$("$AAPT" dump badging "$APK" 2>/dev/null | grep -m1 '^package:' \
      | sed -E "s/^package: name='([^']+)'.*/\\1/" || true)
    if [ -n "$PKG" ]; then
      pass "package: $PKG"
    else
      warn "could not parse package name from APK"
    fi
  fi
fi

echo "→ checking device reachability…"
DEV_LIST=$("$ADB" devices 2>/dev/null | awk -v d="$DEVICE" '$1 == d {print $2}')
case "$DEV_LIST" in
  device) pass "device $DEVICE online" ;;
  unauthorized) fail "device $DEVICE is UNAUTHORIZED — approve RSA prompt on phone" ;;
  offline) fail "device $DEVICE is OFFLINE — replug cable / adb kill-server" ;;
  "") fail "device $DEVICE not listed in 'adb devices'" ;;
  *) fail "device $DEVICE in unknown state: $DEV_LIST" ;;
esac

if [ "$FAIL" = "0" ]; then
  echo "→ probing device properties…"
  MODEL=$("$ADB" -s "$DEVICE" shell getprop ro.product.model 2>/dev/null | tr -d '\r\n')
  OS_VER=$("$ADB" -s "$DEVICE" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r\n')
  SDK=$("$ADB" -s "$DEVICE" shell getprop ro.build.version.sdk 2>/dev/null | tr -d '\r\n')
  BATT=$("$ADB" -s "$DEVICE" shell dumpsys battery 2>/dev/null | awk -F': ' '/level:/ {print $2}' | head -1 | tr -d '\r\n')
  pass "model: $MODEL · Android $OS_VER (SDK $SDK) · battery $BATT%"
  if [ -n "$BATT" ] && [ "$BATT" -lt 30 ] 2>/dev/null; then
    warn "battery < 30% — plug in before a 1-2h batch"
  fi
fi

echo "→ checking node (for report generator)…"
if ! command -v node >/dev/null 2>&1; then
  fail "node not in PATH"
else
  pass "node: $(node --version)"
fi

echo "→ checking writable runs/ dir…"
RUNS_DIR="$PROJECT_ROOT/runs"
mkdir -p "$RUNS_DIR"
if [ -w "$RUNS_DIR" ]; then
  pass "runs/ writable"
else
  fail "runs/ is not writable"
fi

echo ""
if [ "$FAIL" = "0" ]; then
  printf "\033[32m✓ PREFLIGHT PASSED\033[0m\n"
  exit 0
else
  printf "\033[31m✗ PREFLIGHT FAILED — fix above before running batch\033[0m\n"
  exit 1
fi
