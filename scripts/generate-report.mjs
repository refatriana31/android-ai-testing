#!/usr/bin/env node
// Generate an HTML report from a run directory produced by prepare-run.sh + Claude.
//
// Usage:  node scripts/generate-report.mjs <run-dir>
//
// Expects the following layout inside <run-dir>:
//   meta.json                       (device + apk info — created by prepare-run.sh)
//   test-<id>/steps.json            (per-test log — written by Claude)
//   test-<id>/step-NN.png           (screenshots — captured via `adb exec-out screencap`)
//   test-<id>/video.mp4             (pulled by finalize-test.sh)
//   test-<id>/logcat.filtered.txt   (filtered logcat)
//
// Output:
//   <run-dir>/report.html           (self-contained; open in browser)

import { readFileSync, readdirSync, existsSync, writeFileSync } from 'node:fs';
import { join, basename } from 'node:path';

const runDir = process.argv[2];
if (!runDir) {
  console.error('usage: generate-report.mjs <run-dir>');
  process.exit(1);
}

const metaPath = join(runDir, 'meta.json');
if (!existsSync(metaPath)) {
  console.error(`meta.json not found in ${runDir}`);
  process.exit(1);
}

const meta = JSON.parse(readFileSync(metaPath, 'utf8'));

const testDirs = readdirSync(runDir)
  .filter((n) => n.startsWith('test-'))
  .sort()
  .map((n) => join(runDir, n));

const tests = testDirs.map((tdir) => {
  const dirName = basename(tdir);
  const stepsPath = join(tdir, 'steps.json');
  const video = existsSync(join(tdir, 'video.mp4')) ? 'video.mp4' : null;
  let logcat = '';
  const logcatPath = join(tdir, 'logcat.filtered.txt');
  if (existsSync(logcatPath)) {
    const raw = readFileSync(logcatPath, 'utf8');
    logcat = raw.split('\n').slice(-200).join('\n');
  }
  if (!existsSync(stepsPath)) {
    return {
      id: dirName.replace(/^test-/, ''),
      title: dirName,
      status: 'unknown',
      steps: [],
      video,
      logcat,
      dirName,
      error: 'steps.json missing — test did not produce a step log',
    };
  }
  const data = JSON.parse(readFileSync(stepsPath, 'utf8'));
  return { ...data, video, logcat, dirName };
});

const counts = { passed: 0, failed: 0, error: 0, unknown: 0 };
for (const t of tests) counts[t.status] = (counts[t.status] || 0) + 1;
const total = tests.length;
const totalMs = tests.reduce((a, t) => a + (t.duration_ms || 0), 0);

const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[c]));

const fmtMs = (ms) => {
  if (!ms && ms !== 0) return '';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
};

const fmtMB = (b) => (b ? (b / 1024 / 1024).toFixed(1) + ' MB' : '—');

const renderStep = (s, i, dirName) => {
  const st = s.status || 'unknown';
  const shot = s.screenshot
    ? `<img class="step-thumb" src="${esc(dirName)}/${esc(s.screenshot)}" alt="step ${i + 1}" onclick="openLb('${esc(dirName)}/${esc(s.screenshot)}')">`
    : '<div class="step-thumb placeholder">no image</div>';
  const note = s.note
    ? `<div class="step-note">${esc(s.note)}</div>`
    : '';
  return `
    <div class="step">
      <div class="step-num">${i + 1}</div>
      <div class="step-desc">
        <div>${esc(s.description || s.action || '(no description)')}</div>
        ${note}
      </div>
      ${shot}
      <div class="step-meta">
        <span class="badge ${st}">${st.toUpperCase()}</span>
        <div class="muted mono">${fmtMs(s.duration_ms)}</div>
      </div>
    </div>`;
};

const renderTest = (t) => {
  const st = t.status || 'unknown';
  const videoBlock = t.video
    ? `<video controls preload="metadata" src="${esc(t.dirName)}/${esc(t.video)}"></video>`
    : '<div class="muted">No video captured.</div>';
  const stepsBlock = (t.steps || [])
    .map((s, i) => renderStep(s, i, t.dirName))
    .join('');
  const errorBlock = t.error
    ? `<div class="error"><strong>Error:</strong> ${esc(t.error)}</div>`
    : '';
  const logcatBlock = t.logcat
    ? `<details class="sub"><summary>Logcat (filtered, last 200 lines)</summary><pre class="logcat">${esc(t.logcat)}</pre></details>`
    : '';
  const scenarioBlock = t.scenario_file
    ? `<p class="muted small">Scenario source: <span class="mono">${esc(t.scenario_file)}</span></p>`
    : '';
  return `
  <details ${st === 'failed' || st === 'error' ? 'open' : ''}>
    <summary>
      <span class="badge ${st}">${st.toUpperCase()}</span>
      <span class="test-title">${esc(t.title || t.id || t.dirName)}</span>
      <span class="muted mono duration">${fmtMs(t.duration_ms)}</span>
    </summary>
    <div class="test-body">
      ${errorBlock}
      ${videoBlock}
      <div class="steps">${stepsBlock}</div>
      ${logcatBlock}
      ${scenarioBlock}
    </div>
  </details>`;
};

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Android Test Report — ${esc(meta.run_id)}</title>
<style>
  :root {
    --bg: #0d1117; --panel: #161b22; --panel2: #0b1018; --border: #30363d;
    --fg: #e6edf3; --muted: #8b949e; --accent: #58a6ff;
    --pass: #3fb950; --fail: #f85149; --warn: #d29922; --unknown: #8b949e;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: var(--bg); color: var(--fg); line-height: 1.5; font-size: 14px; }
  .container { max-width: 1200px; margin: 0 auto; padding: 28px 24px 60px; }
  h1 { margin: 0 0 4px; font-size: 26px; font-weight: 600; }
  h2 { margin: 0 0 12px; font-size: 16px; font-weight: 600; color: var(--muted);
       text-transform: uppercase; letter-spacing: 0.5px; }
  .muted { color: var(--muted); }
  .small { font-size: 12px; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, "Courier New", monospace; }
  .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
             gap: 12px; margin: 22px 0; }
  .card { background: var(--panel); border: 1px solid var(--border);
          border-radius: 10px; padding: 16px 18px; }
  .card .info-label { color: var(--muted); font-size: 11px; text-transform: uppercase;
                      letter-spacing: 0.6px; margin-bottom: 4px; }
  .card .big { font-size: 30px; font-weight: 600; line-height: 1.1; }
  .pass-color { color: var(--pass); }
  .fail-color { color: var(--fail); }
  .env-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
              gap: 14px 20px; font-size: 13px; }
  .env-grid > div > .info-label { color: var(--muted); font-size: 11px;
              text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px;
           font-weight: 700; letter-spacing: 0.5px; }
  .badge.passed { background: rgba(63,185,80,0.2); color: var(--pass); }
  .badge.failed { background: rgba(248,81,73,0.2); color: var(--fail); }
  .badge.error { background: rgba(248,81,73,0.3); color: var(--fail); }
  .badge.unknown { background: rgba(210,153,34,0.2); color: var(--warn); }
  details { background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
            margin-bottom: 14px; overflow: hidden; }
  details > summary { padding: 14px 18px; cursor: pointer; display: flex;
                      align-items: center; gap: 12px; font-weight: 500; list-style: none; }
  details > summary::-webkit-details-marker { display: none; }
  details > summary::before { content: '▸'; color: var(--muted); transition: transform 0.15s;
                              font-size: 11px; }
  details[open] > summary::before { transform: rotate(90deg); }
  details > summary .test-title { flex: 1; }
  details > summary .duration { font-size: 12px; }
  .test-body { padding: 0 18px 18px; border-top: 1px solid var(--border); }
  .test-body video { display: block; width: 100%; max-width: 520px; border-radius: 8px;
                     background: #000; margin: 14px 0 8px; }
  .steps { margin-top: 14px; }
  .step { display: grid; grid-template-columns: 32px 1fr 90px 120px; gap: 14px;
          align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border); }
  .step:last-child { border-bottom: none; }
  .step-num { color: var(--muted); font-size: 12px; text-align: right; font-family: ui-monospace, monospace; }
  .step-desc { font-size: 13px; }
  .step-note { color: var(--muted); font-size: 11px; margin-top: 2px; font-style: italic; }
  .step-thumb { width: 90px; height: 135px; object-fit: cover; object-position: top;
                border-radius: 4px; cursor: pointer; background: #000;
                border: 1px solid var(--border); }
  .step-thumb.placeholder { display: flex; align-items: center; justify-content: center;
                            color: var(--muted); font-size: 10px; cursor: default; }
  .step-meta { display: flex; flex-direction: column; gap: 4px; align-items: flex-end; }
  .logcat { background: #010409; padding: 12px; border-radius: 6px; font-size: 11px;
            max-height: 320px; overflow: auto; white-space: pre; color: #c9d1d9;
            margin: 8px 0 0; }
  details.sub { background: var(--panel2); margin: 12px 0 0; border-radius: 6px; }
  details.sub > summary { padding: 10px 14px; font-size: 13px; }
  .error { background: rgba(248,81,73,0.1); border-left: 3px solid var(--fail);
           padding: 10px 14px; margin: 14px 0 0; border-radius: 4px; }
  .lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.92); display: none;
              align-items: center; justify-content: center; z-index: 100; cursor: zoom-out; }
  .lightbox.open { display: flex; }
  .lightbox img { max-width: 92vw; max-height: 92vh; border-radius: 4px; }
  footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border);
           color: var(--muted); font-size: 12px; text-align: center; }
  @media (max-width: 720px) {
    .step { grid-template-columns: 26px 1fr; }
    .step-thumb, .step-meta { grid-column: 2; }
  }
</style>
</head>
<body>
<div class="container">
  <h1>Android Test Report</h1>
  <p class="muted mono small">${esc(meta.run_id)} · started ${esc(meta.started_at)}</p>

  <div class="summary">
    <div class="card">
      <div class="info-label">Total</div>
      <div class="big">${total}</div>
    </div>
    <div class="card">
      <div class="info-label">Passed</div>
      <div class="big pass-color">${counts.passed || 0}</div>
    </div>
    <div class="card">
      <div class="info-label">Failed</div>
      <div class="big fail-color">${(counts.failed || 0) + (counts.error || 0)}</div>
    </div>
    <div class="card">
      <div class="info-label">Duration</div>
      <div class="big">${(totalMs / 1000).toFixed(1)}<span class="muted small" style="font-size:14px;font-weight:400">s</span></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:24px">
    <h2>Environment</h2>
    <div class="env-grid">
      <div><div class="info-label">Device</div>${esc(meta.device.brand || '')} ${esc(meta.device.model || '')}</div>
      <div><div class="info-label">Serial</div><span class="mono">${esc(meta.device.serial || '')}</span></div>
      <div><div class="info-label">Android</div>${esc(meta.device.android_version || '—')} (SDK ${esc(meta.device.sdk || '—')})</div>
      <div><div class="info-label">Screen</div>${esc(meta.device.screen_size || '—')} @ ${esc(meta.device.density || '—')} dpi</div>
      <div><div class="info-label">Build</div><span class="mono">${esc(meta.device.build || '—')}</span></div>
      <div><div class="info-label">Package</div><span class="mono">${esc(meta.apk.package || '—')}</span></div>
      <div><div class="info-label">Version</div>${esc(meta.apk.version_name || '—')} (${esc(meta.apk.version_code || '—')})</div>
      <div><div class="info-label">APK Size</div>${fmtMB(meta.apk.size_bytes)}</div>
    </div>
  </div>

  <h2 style="margin-bottom:14px">Tests</h2>
  ${tests.length === 0 ? '<p class="muted">No tests found in this run.</p>' : tests.map(renderTest).join('')}

  <footer>
    Generated ${new Date().toISOString()} · Android AI Testing · mobile-mcp + Claude Code
  </footer>
</div>

<div class="lightbox" id="lb" onclick="this.classList.remove('open')">
  <img id="lbimg" alt="">
</div>
<script>
  function openLb(src) {
    document.getElementById('lbimg').src = src;
    document.getElementById('lb').classList.add('open');
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') document.getElementById('lb').classList.remove('open');
  });
</script>
</body>
</html>
`;

const outPath = join(runDir, 'report.html');
writeFileSync(outPath, html);
console.log(outPath);
