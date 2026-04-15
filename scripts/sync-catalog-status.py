#!/usr/bin/env python3
"""Sync a run's per-test results back into tests/catalog.csv.

Reads each `test-*/steps.json` in the given run directory, looks up the
corresponding scenario's `uat_id` from `tests/<id>.md`, then updates the
catalog row's Status / Actual Result / Execution Date / Tester columns.

Usage:
  scripts/sync-catalog-status.py                 # pick latest runs/* dir
  scripts/sync-catalog-status.py <run_dir>       # explicit run dir
  scripts/sync-catalog-status.py --dry-run       # preview changes only

Env:
  TESTER   Name written into the Tester column (default: 'Iis Netpolitan').
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

STATUS_MAP = {
    "passed":  "Passed",
    "failed":  "Failed",
    "skipped": "Skipped",
    "error":   "Error",
}

def find_latest_run(runs_root: Path) -> Path | None:
    cand = [p for p in runs_root.iterdir() if p.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}_", p.name)]
    return max(cand, key=lambda p: p.name) if cand else None

def load_scenario_uat(tests_dir: Path, test_id: str) -> str | None:
    p = tests_dir / f"{test_id}.md"
    if not p.is_file():
        return None
    m = re.search(r"^uat_id:\s*(\S+)", p.read_text(), re.MULTILINE)
    return m.group(1) if m else None

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    runs_root = project_root / "runs"
    tests_dir = project_root / "tests"
    catalog = tests_dir / "catalog.csv"

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv[1:]

    if args:
        run_dir = Path(args[0]).resolve()
    else:
        run_dir = find_latest_run(runs_root)
        if not run_dir:
            print(f"ERROR: no run directories under {runs_root}", file=sys.stderr)
            return 2
    if not run_dir.is_dir():
        print(f"ERROR: run_dir not a directory: {run_dir}", file=sys.stderr)
        return 2

    exec_date = run_dir.name[:10]
    tester = os.environ.get("TESTER", "Iis Netpolitan")

    # Collect results keyed by UAT ID
    results: dict[str, dict] = {}
    for tdir in sorted(run_dir.glob("test-*")):
        sj = tdir / "steps.json"
        if not sj.is_file():
            continue
        try:
            data = json.loads(sj.read_text())
        except Exception as e:
            print(f"WARN: skip {tdir.name}: {e}", file=sys.stderr)
            continue
        tid = data.get("id")
        if not tid:
            continue
        uat = load_scenario_uat(tests_dir, tid)
        if not uat:
            continue  # custom scenarios without a UAT ID (smoke, navigation)
        status = STATUS_MAP.get(data.get("status", ""), data.get("status", ""))
        err = data.get("error") or ""
        results[uat] = {
            "status": status,
            "actual": err or ("As expected" if status == "Passed" else ""),
            "date":   exec_date,
            "tester": tester,
            "test":   tid,
        }

    if not results:
        print(f"No UAT-tagged results found under {run_dir}")
        return 0

    # Load catalog
    with catalog.open() as f:
        rows = list(csv.reader(f))
    header = rows[0]
    col = {name: header.index(name) for name in header}

    needed = ["UAT ID", "Status", "Actual Result", "Execution Date", "Tester"]
    for n in needed:
        if n not in col:
            print(f"ERROR: catalog missing column '{n}'", file=sys.stderr)
            return 3

    touched = 0
    unmatched = set(results.keys())
    for i in range(1, len(rows)):
        uat = rows[i][col["UAT ID"]]
        if uat in results:
            r = results[uat]
            new_status = r["status"]
            new_actual = r["actual"]
            # Only write if different — keeps diffs minimal
            changed = False
            if rows[i][col["Status"]] != new_status:
                rows[i][col["Status"]] = new_status; changed = True
            if rows[i][col["Actual Result"]] != new_actual:
                rows[i][col["Actual Result"]] = new_actual; changed = True
            if rows[i][col["Execution Date"]] != r["date"]:
                rows[i][col["Execution Date"]] = r["date"]; changed = True
            if rows[i][col["Tester"]] != r["tester"]:
                rows[i][col["Tester"]] = r["tester"]; changed = True
            if changed:
                touched += 1
                print(f"  {uat:14} → {new_status:8} (from test-{r['test']})")
            unmatched.discard(uat)

    if unmatched:
        print(f"\nWARN: {len(unmatched)} UAT IDs from run not found in catalog:", file=sys.stderr)
        for u in sorted(unmatched):
            print(f"  {u}", file=sys.stderr)

    if dry_run:
        print(f"\nDRY RUN — would update {touched} rows in {catalog}")
        return 0

    if touched == 0:
        print(f"No rows needed updating.")
        return 0

    with catalog.open("w", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerows(rows)
    print(f"\nUpdated {touched} rows in {catalog}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
