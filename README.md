# Android AI Testing

End-to-end APK testing via AI, using `@mobilenext/mobile-mcp` + Claude Code
against a physical Android device over USB/ADB. Produces a TestSprite-style
HTML report with screenshots, per-test videos, logcat, and device info.

**Why this exists:** write tests in plain English Markdown, let Claude execute
them on a real device, get a portable HTML report. Token cost is minimal because
all artifact capture (video, screenshots, logcat) is pure ADB — only the
"decide which button to tap" step uses AI.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Lifecycle of a Test Run](#lifecycle-of-a-test-run)
- [Stopping a Test Mid-Run](#stopping-a-test-mid-run)
- [Adding a New Scenario](#adding-a-new-scenario)
- [Re-running Later (Resuming)](#re-running-later-resuming)
- [Reading the Report](#reading-the-report)
- [Configuration & Overrides](#configuration--overrides)
- [Token Efficiency](#token-efficiency)
- [Troubleshooting](#troubleshooting)
- [Limits](#limits)

---

## Prerequisites

- macOS (paths in scripts/CLAUDE.md are macOS — adapt for Linux/Windows)
- Physical Android device with **USB debugging** enabled, connected via USB
- Android SDK `platform-tools` (for `adb`) and `build-tools` (for `aapt`)
- Node.js ≥ 22 (mobile-mcp requirement)
- Claude Code CLI

Verify the device is reachable:
```
/Users/netpolitan/Library/Android/sdk/platform-tools/adb devices
```
You should see `QSVKHASG6H5LMFKN  device` (not `unauthorized` / `offline`).

---

## Project Structure

```
.
├── app-release.apk             ← your APK under test (gitignored)
├── .mcp.json                   ← project-scoped MCP config (auto-loaded by Claude)
├── CLAUDE.md                   ← Claude's runtime instructions (token rules + recipe)
├── README.md                   ← this file
├── package.json                ← marks repo as ESM for the report generator
├── tests/                      ← scenarios in plain-English Markdown
│   ├── _template.md            ← copy this to author new scenarios
│   ├── 01-smoke.md             ← "app launches without crash"
│   ├── 02-navigation.md        ← "back button navigation works"
│   ├── 03-login-valid.md       ← login with valid credentials
│   └── 04-login-invalid.md     ← login with bad password shows error
├── scripts/
│   ├── prepare-run.sh          ← create run dir, capture device/APK info, start video & logcat
│   ├── finalize-test.sh        ← stop video, pull mp4, filter logcat
│   ├── cleanup.sh              ← safely stop screenrecord / logcat / pid markers
│   └── generate-report.mjs     ← build TestSprite-style HTML from artifacts
└── runs/                       ← per-run artifacts (gitignored)
    └── <YYYY-MM-DD_HH-MM-SS>/
        ├── meta.json
        ├── test-<id>/
        │   ├── steps.json      ← per-step log written by Claude
        │   ├── step-NN.png     ← screenshots (zero-token)
        │   ├── video.mp4
        │   └── logcat.filtered.txt
        └── report.html         ← open in browser
```

---

## Quick Start

```bash
# 1. cd into the project and start Claude Code (loads .mcp.json automatically)
cd "/Users/netpolitan/Desktop/Android AI Testing" && claude
```

Then in the Claude session, just say what you want:

| You say                      | Claude does                                                |
|------------------------------|------------------------------------------------------------|
| "run all tests"              | Every `tests/*.md` (except `_template.md`), one report     |
| "run smoke"                  | Just `tests/01-smoke.md`                                   |
| "run 03-login-valid"         | That one scenario only                                     |
| "re-run failed from last"    | Read latest `runs/*/`, repeat any test where status ≠ passed |
| "show last report"           | Print the `open …/report.html` command                     |
| "stop"                       | Halts the current step (you may need to run cleanup, see below) |

---

## Lifecycle of a Test Run

For each scenario, Claude follows this exact recipe (defined in `CLAUDE.md`):

1. **Prepare** — `bash scripts/prepare-run.sh <test-id> [run-dir]`
   - Creates `runs/<timestamp>/test-<id>/`
   - Captures device info (model, Android version, resolution) into `meta.json`
   - Captures APK info (package, version) via `aapt`
   - Starts `screenrecord` (detached on-device) and `adb logcat` (background local)

2. **Reset state** — `adb shell pm clear <package>` so each scenario starts clean.

3. **Execute steps** — Claude walks the scenario, using the cheapest possible
   tool per step:
   - `mobile_list_elements_on_screen` → JSON UI tree (low token)
   - `mobile_click_on_screen_at_coordinates`, `mobile_type_keys`, `mobile_press_button`
   - Per step, capture an artifact screenshot via bash:
     `adb exec-out screencap -p > step-NN.png` (**0 tokens**)

4. **Write `steps.json`** — Claude logs each step's description, screenshot
   filename, status, duration, and any note.

5. **Finalize** — `bash scripts/finalize-test.sh <test-dir> <status>`
   - Sends SIGINT to on-device `screenrecord` so the mp4 finalizes cleanly
   - Pulls `video.mp4` to the test dir
   - Stops the local logcat process and filters by app package

6. **Repeat** — for the next scenario, prepare-run.sh is called again with the
   same `run-dir` so they share one report.

7. **Generate report** — `node scripts/generate-report.mjs <run-dir>` →
   `report.html` (self-contained, open in any browser).

---

## Stopping a Test Mid-Run

You may want to abort a test (wrong scenario, app froze, you saw something
broken and want to investigate, etc.).

### From Claude Code
- Press **`Esc`** (interrupts the current tool call) — usually enough.
- Or simply type **"stop"** in the chat — Claude will halt.

### Then run cleanup (ALWAYS recommended after a stop)

```bash
bash scripts/cleanup.sh
```

This safely:
1. Sends SIGINT to on-device `screenrecord` (so the mp4 finalizes properly)
2. Removes leftover `/sdcard/current.mp4` from the device
3. Kills any lingering local `adb logcat` processes for your device
4. Deletes `.recordpid` / `.logcatpid` marker files from `runs/`

The script is **idempotent** — safe to run any time, even if nothing's running.

### Exiting the Claude session
- Type `/exit`, or press `Ctrl+C` twice.
- The `.mcp.json` (mobile-mcp server) will be torn down automatically.

### Aborted run artifacts
Even if you stop mid-test, the partially-captured `runs/<timestamp>/` folder
still has whatever screenshots, logcat, and partial video were written. You
can manually run `node scripts/generate-report.mjs runs/<timestamp>` to render
a partial report — useful for forensics.

---

## Adding a New Scenario

Scenarios are plain Markdown files in `tests/`. Naming convention:
**`NN-short-name.md`** where `NN` is a 2-digit ordering prefix.

### Step 1 — Copy the template
```bash
cp tests/_template.md tests/05-my-feature.md
```

### Step 2 — Fill in the file
```markdown
---
id: 05-my-feature                        # MUST match filename (no .md)
title: One-line description for the report
priority: medium                          # informational only
timeout_seconds: 120                      # informational only
---

## Setup
- Any preconditions (e.g. "user is logged in", "on home screen")
- Any env vars you reference ($TEST_USER, $SITE_NAME, etc.)

## Steps
1. Plain-English action #1 (e.g. "Tap the 'Profile' tab in bottom nav")
2. Action #2
3. ...

## Expected
- Observable outcome #1 (verifiable via UI tree → cheap)
- Observable outcome #2 (verifiable via logcat → free)
- Last resort: "screenshot shows X" (uses vision tokens — avoid if possible)

## Notes (optional)
- Hints, known-stable coordinates, things to watch out for.
```

### Step 3 — Tips for writing good scenarios

- **Be specific about labels** — write `"Tap 'Login' button"` not `"Tap login"`.
  Claude searches the UI tree by label/text exact-or-substring match.
- **One step = one user-visible action**, not "tap email + type + tap pw + type".
  Granular steps make better screenshots and easier debugging.
- **Verifications go in `## Expected`**, not in steps. Steps describe actions;
  Expected describes how Claude knows it worked.
- **Prefer cheap assertions** (UI tree contains "X", logcat has no FATAL) over
  vision ("screenshot looks right"). Saves tokens.
- **For login-gated flows**: include `Setup` instructions to either reset state
  (`adb shell pm clear …`) or run a precondition scenario first.
- **Don't hardcode credentials** — use `$TEST_USER` / `$TEST_PASS` references
  in the `.md`. The actual values stay in env vars or the chat session.

### Step 4 — Run it

In Claude Code session:
```
run 05-my-feature
```
or just `run all tests`.

### Examples to learn from

- `tests/01-smoke.md` — minimal scenario (launch + don't crash)
- `tests/03-login-valid.md` — multi-screen flow with credential typing
- `tests/04-login-invalid.md` — error-path verification (still on screen + error visible)

---

## Re-running Later (Resuming)

This project is **stateless between sessions** — there is nothing to "resume",
you just start fresh.

### Each session you do:
1. Connect Android device via USB → confirm `adb devices` shows it.
2. Open the project in Claude Code:
   ```
   cd "/Users/netpolitan/Desktop/Android AI Testing" && claude
   ```
3. (If credentials are needed) Tell Claude in chat: *"the test creds are
   user=Iis_Netpolitan pass=iis123Aa site=permata-revamp-stg"*. Claude uses
   them only for the current session — they're not persisted.
4. Ask Claude to run tests as before.

### Older runs stay in `runs/`
Every previous run lives in its own timestamped folder. To revisit:
```bash
# List all past runs (newest first)
ls -t runs/

# Open a specific report
open runs/2026-04-15_16-24-32/report.html
```

You can clean up old runs anytime — they're gitignored:
```bash
rm -rf runs/*
```

### After modifying scripts / CLAUDE.md
If you change `.mcp.json` or `CLAUDE.md` while a Claude Code session is open,
**restart the session** (`/exit` then `claude`) so the new config takes effect.
Changes to `tests/*.md` and `scripts/*.sh` are picked up immediately — no
restart needed.

---

## Reading the Report

Open `runs/<timestamp>/report.html` in any browser. Sections:

- **Header**: run timestamp, total/passed/failed counts, total duration
- **Environment card**: device model, Android version, screen size + density,
  APK package + version + size
- **Per-test cards** (collapsible — failed tests auto-expanded):
  - Status badge (PASSED / FAILED / ERROR / UNKNOWN)
  - Embedded video player (the full screen recording)
  - Step-by-step timeline: number, description, screenshot thumbnail (click to
    zoom), status badge, duration. Notes shown in italic below description.
  - Collapsible "Logcat (filtered)" — last 200 lines, filtered to your app's
    package + crash markers
- **Footer**: generation timestamp + tooling info

The HTML is self-contained except for the screenshots/video which are referenced
relatively. To share, zip the entire `runs/<timestamp>/` folder and the report
will work offline.

---

## Configuration & Overrides

All scripts honor these env vars (defaults shown):

| Env var   | Default                                                       | Purpose                          |
|-----------|---------------------------------------------------------------|----------------------------------|
| `DEVICE`  | `QSVKHASG6H5LMFKN`                                            | adb serial of target device       |
| `APK`     | `./app-release.apk`                                           | Path to APK file                  |
| `ADB`     | `/Users/netpolitan/Library/Android/sdk/platform-tools/adb`    | Path to adb binary                |
| `AAPT`    | `/Users/netpolitan/Library/Android/sdk/build-tools/37.0.0/aapt` | Path to aapt binary             |

Examples:
```bash
# Test against a different connected device
DEVICE=R58M37ABCDE bash scripts/prepare-run.sh 01-smoke

# Test a different APK without renaming the file
APK=/path/to/release.apk bash scripts/prepare-run.sh 01-smoke
```

The `.mcp.json` env block also sets `ANDROID_HOME` so mobile-mcp finds adb:
```json
{
  "mcpServers": {
    "mobile-mcp": {
      "command": "npx",
      "args": ["-y", "@mobilenext/mobile-mcp@latest"],
      "env": {
        "MOBILEMCP_DISABLE_TELEMETRY": "1",
        "ANDROID_HOME": "/Users/netpolitan/Library/Android/sdk"
      }
    }
  }
}
```

---

## Token Efficiency

AI tokens are spent **only** when Claude reads your scenario and decides which
element to interact with. Everything else is zero-token bash:

| Operation                        | Mechanism                                          | Tokens |
|----------------------------------|----------------------------------------------------|--------|
| Decisions (find button, verify)  | `mobile_list_elements_on_screen` (JSON UI tree)    | low    |
| Report screenshots               | `adb exec-out screencap -p > step-NN.png`          | **0**  |
| Video recording                  | `adb shell screenrecord` (on-device)               | **0**  |
| Logcat capture                   | `adb logcat > file` (background)                   | **0**  |
| Device info (model, version, …)  | `adb shell getprop` (in `prepare-run.sh`)          | **0**  |
| APK info (package, version)      | `aapt dump badging` (in `prepare-run.sh`)          | **0**  |
| HTML report rendering            | `node scripts/generate-report.mjs`                 | **0**  |

Vision (`mobile_take_screenshot` returning base64 to Claude) is reserved as a
**fallback** — only when the UI tree gives no actionable info (custom canvas,
splash animations). When used, it's logged in the step's `note` field as
`"vision fallback: <reason>"` so you can audit token cost from the report.

The full ruleset Claude follows is in [`CLAUDE.md`](./CLAUDE.md).

---

## Troubleshooting

| Symptom                                  | Cause / Fix                                                                 |
|------------------------------------------|------------------------------------------------------------------------------|
| `mobile_*` tools not available in Claude | Restart session in this folder so `.mcp.json` loads                          |
| `adb: device offline`                     | `adb kill-server && adb start-server`; reconnect cable; replug device         |
| Multiple devices, ambiguous adb          | Always pass `-s "$DEVICE"` (scripts already do this)                         |
| `video.mp4` is 0 bytes                   | Test was < 2s. Add a small `sleep` before `finalize`. Or accept missing video |
| `screenrecord` won't start               | Run `bash scripts/cleanup.sh` to clear stale processes, retry                 |
| Login screen never appears               | `adb shell pm clear <package>` to reset app state                            |
| Test hangs forever                       | `Esc` in Claude → `bash scripts/cleanup.sh` → start fresh                    |
| Report shows wrong package name          | Bug in `aapt` parsing — was fixed; if it returns, regenerate from `meta.json` |
| `pm clear` fails (permission denied)     | Some apps with device-admin can't be cleared — uninstall + reinstall instead |

### Manual sanity check (no Claude needed)
```bash
# Are scripts working independently?
cd "/Users/netpolitan/Desktop/Android AI Testing"
bash scripts/prepare-run.sh manual-check
# (do something on phone for ~5 seconds)
RUN_DIR=$(ls -td runs/*/ | head -1)
TEST_DIR="${RUN_DIR}test-manual-check"
echo '{"id":"manual-check","title":"Manual","status":"passed","steps":[],"duration_ms":5000}' > "$TEST_DIR/steps.json"
bash scripts/finalize-test.sh "$TEST_DIR" passed
node scripts/generate-report.mjs "$RUN_DIR"
open "${RUN_DIR}report.html"
```

---

## Limits

- **`screenrecord` 3-minute cap per file** — split long flows into multiple
  scenarios. The next scenario in the same run gets its own video.
- **Single-device, sequential** — no parallel device runs (yet). Multiple devices
  attached: pass `DEVICE` env var to target one specifically.
- **Android only** — mobile-mcp also supports iOS but this project's scripts
  are wired for `adb` only.
- **Vision-fallback cost** — if a scenario forces vision repeatedly (e.g. a
  fully custom-rendered canvas), token usage rises. Watch the `note` fields in
  `steps.json` to spot abusive scenarios.
- **Credentials are not persisted** — by design. Provide them per-session in
  chat, or set env vars before launching Claude:
  ```bash
  export TEST_USER=Iis_Netpolitan TEST_PASS=iis123Aa SITE_NAME=permata-revamp-stg
  claude
  ```

---

## License / Attribution

Built on top of [`@mobilenext/mobile-mcp`](https://github.com/mobile-next/mobile-mcp).
This project is for internal QA use; no external license declared.
