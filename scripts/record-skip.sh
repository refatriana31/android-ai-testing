#!/bin/bash
# Record a scenario as `skipped` without touching the device.
# Used for scenarios whose precondition is known to be unreachable
# (manager persona, email flow, SSO, race-condition, etc.).
#
# Usage: record-skip.sh <run_dir> <test-id> "<reason>"
#
# Assumes prepare-run.sh has NOT been called for this scenario (we handle it).

set -euo pipefail

RUN_DIR="${1:?usage: record-skip.sh <run_dir> <test-id> <reason>}"
TEST_ID="${2:?}"
REASON="${3:?}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call prepare-run to get meta.json + logcat pipeline going (quick).
OUT=$(bash "$SCRIPT_DIR/prepare-run.sh" "$TEST_ID" "$RUN_DIR")
TEST_DIR="$RUN_DIR/test-$TEST_ID"

# Look up title + scenario_file from the scenario md
TESTS_DIR="$(cd "$SCRIPT_DIR/../tests" && pwd)"
MD="$TESTS_DIR/${TEST_ID}.md"
TITLE=$(awk -F': ' '/^title:/{print substr($0, index($0,":")+2); exit}' "$MD")

NOW_Z=$(date -u +%Y-%m-%dT%H:%M:%SZ)

python3 - "$TEST_DIR" "$TEST_ID" "$TITLE" "tests/${TEST_ID}.md" "$NOW_Z" "$REASON" <<'PY'
import sys, json, os
td, tid, title, sf, ts, reason = sys.argv[1:7]
obj = {
  "id": tid,
  "title": title,
  "scenario_file": sf,
  "started_at": ts,
  "ended_at": ts,
  "duration_ms": 0,
  "status": "skipped",
  "error": f"skipped: {reason}",
  "steps": [{
    "description": "Auto-skipped by triage: precondition cannot be satisfied without additional setup",
    "action": "n/a",
    "screenshot": None,
    "status": "skipped",
    "duration_ms": 0,
    "note": reason
  }]
}
open(os.path.join(td, "steps.json"), "w").write(json.dumps(obj, indent=2))
PY

bash "$SCRIPT_DIR/finalize-test.sh" "$TEST_DIR" skipped >/dev/null
echo "skipped  $TEST_ID  ($REASON)"
