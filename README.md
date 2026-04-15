# Android AI Testing

End-to-end APK testing via AI, using `@mobilenext/mobile-mcp` + Claude Code
against a physical Android device over USB/ADB. Produces a TestSprite-style
HTML report with screenshots, per-test videos, logcat, and device info.

## Prerequisites

- macOS (these paths are set for macOS — adapt if on Linux)
- Physical Android device with **USB debugging enabled**, connected over USB
- Android SDK platform-tools (`adb`) and build-tools (`aapt`)
- Node.js ≥ 22 (mobile-mcp requirement)
- Claude Code CLI

## What's Here

```
.
├── app-release.apk              ← your APK under test (put it here)
├── .mcp.json                    ← project-scoped MCP config (auto-loaded by Claude)
├── CLAUDE.md                    ← instructions Claude reads on every session
├── tests/                       ← test scenarios in plain-English Markdown
│   ├── _template.md
│   ├── 01-smoke.md              ← "app launches without crash"
│   └── 02-navigation.md         ← "forward + back button navigation works"
├── scripts/
│   ├── prepare-run.sh           ← device/APK info, start video & logcat
│   ├── finalize-test.sh         ← stop video, pull mp4, filter logcat
│   └── generate-report.mjs      ← TestSprite-style HTML from artifacts
└── runs/                        ← per-run artifacts (gitignored)
    └── 2026-04-15_15-40-00/
        ├── meta.json
        ├── test-01-smoke/
        │   ├── steps.json
        │   ├── step-01.png
        │   ├── video.mp4
        │   └── logcat.filtered.txt
        └── report.html          ← open in browser
```

## Usage

### 1. First-time setup
1. Place your APK at `./app-release.apk` (already done if you see the file).
2. Connect your Android device via USB; ensure it shows up:
   ```
   /Users/netpolitan/Library/Android/sdk/platform-tools/adb devices
   ```
   You should see the serial `device` (not `unauthorized` or `offline`).
3. Open this folder in Claude Code:
   ```
   cd "/Users/netpolitan/Desktop/Android AI Testing" && claude
   ```
   Claude will auto-load `.mcp.json` → mobile-mcp tools become available.

### 2. Running tests
Just ask Claude in natural language:

- **"run all tests"** — runs every `tests/*.md` (except `_template.md`)
- **"run smoke test"** — runs `tests/01-smoke.md`
- **"run 02-navigation"** — runs that specific scenario
- **"show last report"** — prints a command to open the latest report

Claude will:
1. Reinstall the APK for a clean state (`adb uninstall` + `adb install -r -g`)
2. Execute each scenario step-by-step using mobile-mcp tools
3. Record video, logcat, and per-step screenshots to `runs/<timestamp>/`
4. Generate `report.html` at the end — open it in your browser to review

### 3. Writing new scenarios
Copy `tests/_template.md` → `tests/03-your-name.md`, fill in Setup/Steps/Expected
in plain English, save. Then ask Claude to run it.

## Token Efficiency (Why This Project Is Cheap to Run)

AI tokens are only spent when Claude reads your scenario and decides which
element to tap. Everything else is zero-token:

| Operation | Mechanism | Tokens |
|---|---|---|
| Decisions (find button, verify text) | `mobile_list_elements_on_screen` (JSON UI tree) | low |
| Report screenshots | `adb exec-out screencap -p > …` (bash) | **0** |
| Video recording | `adb shell screenrecord` (bash, on-device) | **0** |
| Logcat | `adb logcat > …` (bash) | **0** |
| Device/APK info | `adb getprop`, `aapt dump badging` | **0** |
| HTML report | Node script, no LLM | **0** |

Vision (`mobile_take_screenshot`) is a fallback — Claude only uses it when
the UI tree gives no actionable info (splash animations, custom canvases).

## Overriding Defaults

All scripts honor these env vars:
- `DEVICE` — adb serial (default: `QSVKHASG6H5LMFKN`)
- `APK` — path to APK (default: `./app-release.apk`)
- `ADB` — path to adb binary
- `AAPT` — path to aapt binary

Example: test against a different device:
```
DEVICE=emulator-5554 bash scripts/prepare-run.sh 01-smoke
```

## Limits

- `screenrecord` has a 3-minute max per file. Split longer flows into multiple scenarios.
- Currently single-device, sequential execution (no parallel devices).
- Android only (mobile-mcp also supports iOS but not wired in here).
