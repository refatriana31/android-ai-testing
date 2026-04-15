#!/usr/bin/env python3
"""Generate scenario markdown files under tests/ for catalog rows that don't
have a scenario yet.

Usage:
  scripts/scaffold-from-catalog.py --priority High           # scaffold all High uncovered
  scripts/scaffold-from-catalog.py --priority Medium
  scripts/scaffold-from-catalog.py --priority High --dry-run

Filenames are auto-assigned: starts from the highest existing NN+1 and walks
up. UAT IDs are converted to lowercase-hyphen for the filename slug.
"""
import argparse
import csv
import os
import re
import sys
from pathlib import Path

TIMEOUTS_BY_TYPE = {"Positive": 90, "Negative": 90, "Edge": 120}
PRIORITY_MAP = {"High": "high", "Medium": "medium", "Low": "low"}

def existing_covered(tests_dir: Path) -> set[str]:
    covered = set()
    for p in tests_dir.glob("[0-9][0-9]-*.md"):
        m = re.search(r"^uat_id:\s*(\S+)", p.read_text(), re.MULTILINE)
        if m:
            covered.add(m.group(1))
    return covered

def next_file_number(tests_dir: Path) -> int:
    nums = []
    for p in tests_dir.glob("[0-9][0-9]-*.md"):
        m = re.match(r"(\d+)-", p.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1

def split_steps(raw: str) -> list[str]:
    if not raw:
        return ["Perform the action described in the UAT scenario"]
    lines = [ln.strip() for ln in raw.replace("\r", "").split("\n") if ln.strip()]
    return lines or ["Perform the action described in the UAT scenario"]

def slugify(uat_id: str) -> str:
    return uat_id.lower().replace("_", "-")

def render_scenario(n: int, row: dict) -> tuple[str, str]:
    uat = row["UAT ID"]
    slug = slugify(uat)
    fname = f"{n:02d}-{slug}.md"
    pri = PRIORITY_MAP.get(row["Priority"], "medium")
    typ = row["Scenario Type"] or "Positive"
    timeout = TIMEOUTS_BY_TYPE.get(typ, 90)
    persona = row["Persona"] or "Learner"

    title = row["Scenario"].strip() or f"Scenario for {uat}"
    title = " ".join(title.split())  # collapse whitespace/newlines

    steps_csv = split_steps(row["Test Steps"])
    expected = " ".join((row["Expected Result"] or "").split()) or "Behaves as described in the UAT row."
    precondition = " ".join((row["Precondition"] or "").split()) or "Learner is logged in"

    # Manager persona hint
    persona_note = ""
    if "Manager" in persona:
        persona_note = (
            "- **Manager persona required**: `$TEST_USER` for this test must be a manager "
            "account. If only the default learner account is available, record status "
            "`skipped` with note `precondition not met: manager account unavailable`.\n"
        )

    # Build step list — steps 1-5 are the common onboarding prefix, then UAT steps
    uat_steps_numbered = "\n".join(
        f"{i+6}. {s}" for i, s in enumerate(steps_csv)
    )

    body = f"""---
id: {n:02d}-{slug}
title: {title}
priority: {pri}
timeout_seconds: {timeout}
uat_id: {uat}
section: {row['Section']}
persona: {persona}
---

## Setup
- Reset app state: `adb shell pm clear com.example.bawana_revamp`
- Site name via `$SITE_NAME` (default: `permata-revamp-stg`)
- Login via `$TEST_USER` / `$TEST_PASS`
- Precondition (from UAT): {precondition}
{persona_note}
## Steps
1. Launch app after `pm clear`
2. Enter site name and tap Next
3. Login with credentials
4. Handle onboarding (language → Confirm; skip assessment if prompted)
5. Ensure Home tab is active
{uat_steps_numbered}

## Expected
- UAT expected: {expected}
- Verify via UI tree (`mobile_list_elements_on_screen`) — prefer label/text match over vision.
- No `FATAL EXCEPTION` in `logcat.filtered.txt`.

## Notes
- Auto-generated from UAT catalog row {uat}. Refine wording as needed.
- If feature is gated by data (assignments, events, interests, roles) and data is absent, record status `skipped` with note `precondition not met: <detail>`.
"""
    return fname, body

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--priority", required=True, choices=["High", "Medium", "Low"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="stop after N files")
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"
    catalog = tests_dir / "catalog.csv"

    rows = list(csv.DictReader(catalog.open()))
    covered = existing_covered(tests_dir)

    # Uncovered rows in the requested priority, preserving catalog order
    targets = [r for r in rows
               if r["Priority"] == args.priority
               and r["UAT ID"]
               and r["UAT ID"] not in covered
               and not r["Scenario"].startswith("[PLACEHOLDER]")]
    if args.limit:
        targets = targets[:args.limit]

    if not targets:
        print(f"No uncovered {args.priority}-priority rows to scaffold.")
        return 0

    start_n = next_file_number(tests_dir)
    print(f"Scaffolding {len(targets)} {args.priority}-priority scenarios, starting at {start_n:02d}.\n")

    created = 0
    n = start_n
    for row in targets:
        fname, body = render_scenario(n, row)
        dst = tests_dir / fname
        if dst.exists():
            # Skip if filename collision (shouldn't happen — next_file_number guards)
            print(f"  SKIP {fname} — already exists")
            n += 1
            continue
        if args.dry_run:
            print(f"  would create {fname}  [{row['UAT ID']}]")
        else:
            dst.write_text(body)
            print(f"  created {fname}  [{row['UAT ID']}]")
        created += 1
        n += 1

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}{'Would create' if args.dry_run else 'Created'} {created} scenario files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
