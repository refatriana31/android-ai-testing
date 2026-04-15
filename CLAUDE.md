# Android AI Testing — Claude Instructions

This project runs end-to-end tests against an Android APK on a physical device
using `@mobilenext/mobile-mcp` (loaded automatically from `.mcp.json`) plus
bash scripts that handle zero-token artifact capture (video, logcat, screenshots,
device/APK info).

## Environment (hard-coded defaults)

- **ADB**: `/Users/netpolitan/Library/Android/sdk/platform-tools/adb`
- **AAPT**: `/Users/netpolitan/Library/Android/sdk/build-tools/37.0.0/aapt`
- **Device serial**: `QSVKHASG6H5LMFKN` (physical device)
- **APK**: `./app-release.apk` (at project root)
- All these are overridable via env vars `ADB`, `AAPT`, `DEVICE`, `APK`.

Always pass `-s "$DEVICE"` to every adb invocation — there may be an offline
emulator attached that adb will otherwise refuse to disambiguate.

## Token Efficiency — NON-NEGOTIABLE RULES

These rules minimize AI token spend during test execution.

1. **UI tree first, vision last.** For every decision ("which element to tap?"),
   call `mobile_list_elements_on_screen` FIRST. It returns a JSON tree with
   labels + coordinates — cheap to process. Only fall back to
   `mobile_take_screenshot` (vision) when the tree gives you nothing actionable
   (unlabeled canvas, splash graphics). Log the reason in the step's `note`
   field as `"vision fallback: <reason>"`.

2. **Report screenshots via bash, not via MCP.** Artifact screenshots (visual
   evidence for the HTML report) must NOT go through Claude's context. Capture
   them directly on the shell:
   ```bash
   "$ADB" -s "$DEVICE" exec-out screencap -p > "$TEST_DIR/step-NN.png"
   ```
   Reserve `mobile_take_screenshot` strictly for cases where YOU need to see
   the pixels to decide what to do.

3. **Zero-token operations** — always use bash, never MCP:
   - Device info (`adb shell getprop …`) — done by `prepare-run.sh`
   - APK info (`aapt dump badging`) — done by `prepare-run.sh`
   - Logcat capture — done by `prepare-run.sh` / `finalize-test.sh`
   - Video recording (`adb shell screenrecord`) — done by the scripts
   - HTML report rendering — done by `generate-report.mjs`

4. **Reuse stable coordinates.** If a scenario step provides explicit
   coordinates, tap them directly without re-dumping the UI tree.

5. **Verify assertions cheaply.**
   - "Element present/absent" → UI tree contains check (free-ish)
   - "App is foreground" → `adb shell dumpsys activity activities | grep mResumedActivity`
   - "No crash" → grep `logcat.filtered.txt` for `FATAL EXCEPTION|ANR in`
   - Only fall back to vision to verify something explicitly visual
     (e.g., "button is red", "image is centered").

6. **Write scenarios tersely.** Steps are instructions, not prose. 1 line = 1
   step. No restating context.

## Test Execution Recipe

When user says "run all tests", "run smoke", "run 01-smoke", etc., follow
these steps precisely. Create ONE run directory shared across all tests in
the batch.

### Step 0 — Parse scenarios to run
- List `tests/*.md` (exclude `_template.md`).
- Read frontmatter (`id`, `title`, `timeout_seconds`) and Steps/Expected sections.
- If user asked for a single test, filter to that `id`.

### Step 1 — For the FIRST test, create the run directory

```bash
bash scripts/prepare-run.sh <first-test-id>
```
Capture the JSON output — extract `run_dir` and `test_dir`. `run_dir` is
reused across all tests in this batch.

### Step 2 — Install APK fresh (user chose "reinstall each run")

Read package name from `"$RUN_DIR"/meta.json` (already populated by prepare-run.sh).
Then:

```bash
"$ADB" -s "$DEVICE" uninstall "$PKG" 2>/dev/null || true
"$ADB" -s "$DEVICE" install -r -g "$APK"   # -g auto-grants runtime permissions
```

Do this ONCE per run (before the first scenario). Don't reinstall between
scenarios in the same run — the scenarios should cooperate on a clean install.
If user explicitly wants per-scenario isolation, mention it and wait for confirm.

### Step 3 — Execute scenario steps (per test)

Record `started_at` timestamp. For each step in the scenario:

1. (Optional, if locating) `mobile_list_elements_on_screen` → find target.
2. Perform action via the appropriate mobile-mcp tool:
   - `mobile_launch_app(packageName: …)`
   - `mobile_click_on_screen_at_coordinates(x, y)`
   - `mobile_swipe_on_screen(direction, distance)`
   - `mobile_type_keys(text)`
   - `mobile_press_button("BACK" | "HOME" | "ENTER" | …)`
3. Capture a screenshot via bash (numbered):
   ```bash
   N=$(printf "%02d" $STEP_NUM)
   "$ADB" -s "$DEVICE" exec-out screencap -p > "$TEST_DIR/step-$N.png"
   ```
4. Append a step record to your in-memory list (you will flush to `steps.json`
   at the end).

Record `ended_at` after the last step. Decide `status` based on whether all
expected assertions held.

### Step 4 — Write `steps.json`

Write exactly this shape to `"$TEST_DIR"/steps.json`:

```json
{
  "id": "01-smoke",
  "title": "App launches without crash",
  "scenario_file": "tests/01-smoke.md",
  "started_at": "2026-04-15T15:40:00Z",
  "ended_at": "2026-04-15T15:40:32Z",
  "duration_ms": 32000,
  "status": "passed",
  "error": null,
  "steps": [
    {
      "description": "Launch app via package name",
      "action": "mobile_launch_app",
      "screenshot": "step-01.png",
      "status": "passed",
      "duration_ms": 2100,
      "note": null
    }
  ]
}
```

- `status` values: `"passed"`, `"failed"`, `"error"`, `"skipped"`.
- Use `"skipped"` when a scenario cannot be verified because a **data precondition**
  is not met (no events, no assignments, no unfinished courses to resume, etc.).
  Put the reason in top-level `error`, e.g. `"skipped: learner has no recent activity"`.
  Skipped is NOT pass, NOT fail — it means the test is unverifiable right now.
- Use `"failed"` when the feature is present but behaves incorrectly or an assertion
  fails. Use `"error"` when the test could not run due to infra (crash, malformed
  scenario, tool timeout).
- `error` is a short human-readable message when `status != "passed"`.
- Never emit relative paths for screenshots outside the test dir.
- When a step used vision fallback, set
  `"note": "vision fallback: <short reason>"`.

### Retry on failure (batch runs only)

When running a batch, for any scenario that ends `failed` or `error`, retry it
ONCE. If the retry passes, keep the `passed` result and add a step note
`"flaky: passed on retry"`. If the retry also fails, keep the failure and add
`"retry confirmed failure"`. Don't retry `skipped` — the data-precondition
reason won't disappear on a second run.

### Step 5 — Finalize the test

```bash
bash scripts/finalize-test.sh "$TEST_DIR" <status>
```
This stops video + logcat, pulls `video.mp4`, and writes
`logcat.filtered.txt`. Its `<status>` argument is informational — the
authoritative status is in `steps.json`.

### Step 6 — Next scenario or report

- **If more scenarios**: call `prepare-run.sh <next-id> "$RUN_DIR"` (pass
  existing run_dir so they share one report) and repeat Steps 3–5.
- **If done**: generate the HTML report:
  ```bash
  node scripts/generate-report.mjs "$RUN_DIR"
  ```
  Print the path to the user: "Report: \$RUN_DIR/report.html".

## Common User Requests → What To Do

| User says                          | Action                                                     |
|-----------------------------------|------------------------------------------------------------|
| "run all tests"                   | Every `tests/*.md` except `_template.md`; single run dir.  |
| "run smoke" / "run 01"            | Only `tests/01-smoke.md`.                                  |
| "re-run failures from last"       | Read latest `runs/*/test-*/steps.json`; rerun where `status != passed`. |
| "show last report"                | Print `open "runs/<latest>/report.html"` for user to run.  |
| "open the report"                 | Same as above.                                             |

## Troubleshooting

- **MCP tools not showing up** → user needs to restart Claude Code session
  in this folder so `.mcp.json` loads.
- **`device offline`** → `adb kill-server && adb start-server` then reconnect
  cable. Also check `adb devices` — ignore the emulator-5554 offline entry.
- **`mobile_launch_app` fails** → double-check package name from `meta.json`;
  fall back to `adb shell monkey -p $PKG -c android.intent.category.LAUNCHER 1`.
- **`video.mp4` missing or 0 bytes** → test was < 2 seconds (screenrecord
  couldn't finalize). Either insert a short wait before finalize, or accept
  missing video (report handles it gracefully).
- **Permission dialogs blocking test** → `adb install -r -g` should auto-grant
  runtime permissions (`-g`). If the app prompts for something else, tap
  "Allow" via UI tree interaction and note it in the step log.

## Hard Limits

- `screenrecord --time-limit 180` — max 3 minutes per test mp4. Split
  longer scenarios into multiple test files.
- Don't write into `.mcp.json`, `package.json`, or the scripts during a test
  run — those are setup, not runtime state.
- Don't commit `runs/` (already in `.gitignore`).
