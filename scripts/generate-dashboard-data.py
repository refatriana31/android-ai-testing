#!/usr/bin/env python3
"""Regenerate the __DASHBOARD_DATA__ blob inside dashboard/index.html.

Reads all runs + catalog.csv, builds fresh JSON, and injects it into
the existing index.html template (preserving HTML/CSS/JS).

Also adds Drive video mapping + screenshot paths to each test entry.

Usage:
  scripts/generate-dashboard-data.py
"""
import csv, json, os, re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
runs_dir = root / "runs"
catalog_path = root / "tests" / "catalog.csv"
index_path = root / "dashboard" / "index.html"
drive_map_path = root / "dashboard" / "drive-mapping.json"

# Load Drive mapping
drive_map = {}
if drive_map_path.is_file():
    drive_map = json.loads(drive_map_path.read_text())

# Collect run metadata
runs_data = []
for rd in sorted(runs_dir.iterdir()):
    mf = rd / "meta.json"
    if mf.is_file():
        m = json.loads(mf.read_text())
        runs_data.append(m)

# Collect all test results (latest per test-id wins)
all_tests = {}
for rd in sorted(runs_dir.iterdir()):
    if not rd.is_dir(): continue
    for td in sorted(rd.iterdir()):
        if not td.name.startswith("test-"): continue
        sj = td / "steps.json"
        if not sj.is_file(): continue
        try: data = json.loads(sj.read_text())
        except: continue
        tid = data.get("id", "")
        if not tid: continue

        # Find UAT ID
        md = root / "tests" / f"{tid}.md"
        uat_id = None
        if md.is_file():
            m2 = re.search(r'^uat_id:\s*(\S+)', md.read_text(), re.MULTILINE)
            if m2: uat_id = m2.group(1)

        # Add video + screenshot info
        video_path = td / "video.mp4"
        has_video = video_path.is_file() and video_path.stat().st_size > 0
        screenshots = sorted(td.glob("step-*.png"))

        entry = {
            "id": tid,
            "title": data.get("title", ""),
            "scenario_file": data.get("scenario_file", ""),
            "started_at": data.get("started_at", ""),
            "ended_at": data.get("ended_at", ""),
            "duration_ms": data.get("duration_ms", 0),
            "status": data.get("status", ""),
            "error": data.get("error"),
            "steps": data.get("steps", []),
            "_run": rd.name,
            "_uat_id": uat_id,
        }

        # Drive video or local
        if uat_id and uat_id in drive_map:
            entry["_drive_id"] = drive_map[uat_id]
        elif has_video:
            entry["_video_local"] = f"../runs/{rd.name}/test-{tid}/video.mp4"

        # Screenshots (deployed to dashboard/screenshots/)
        if uat_id and screenshots:
            entry["_screenshots"] = [f"screenshots/{uat_id}/{s.name}" for s in screenshots]

        all_tests[tid] = entry

tests_list = [all_tests[k] for k in sorted(all_tests.keys())]

# Load catalog
catalog = list(csv.DictReader(catalog_path.open()))

# Section map: UAT ID → section
section_map = {r["UAT ID"]: r["Section"] for r in catalog}

# Build DATA object
DATA = {
    "runs": runs_data,
    "total_catalog": len(catalog),
    "tests": tests_list,
    "catalog": catalog,
    "section_map": section_map,
}

# Inject into index.html
content = index_path.read_text()
marker_start = "window.__DASHBOARD_DATA__ = "
marker_end = ";\n</script>"

idx_start = content.index(marker_start) + len(marker_start)
idx_end = content.index(marker_end, idx_start)

new_content = content[:idx_start] + json.dumps(DATA, ensure_ascii=False) + content[idx_end:]
index_path.write_text(new_content)

print(f"Injected {len(tests_list)} tests + {len(catalog)} catalog rows + {len(drive_map)} Drive videos")
print(f"Updated {index_path}")
