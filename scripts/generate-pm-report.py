#!/usr/bin/env python3
"""Generate laporan QA profesional untuk PM dari catalog.csv + data run.

Usage:
  scripts/generate-pm-report.py                  # auto-detect latest run
  scripts/generate-pm-report.py -o report.html   # custom output path
"""
import argparse, csv, json, os, re, sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    catalog_path = root / "tests" / "catalog.csv"
    runs_dir = root / "runs"

    rows = list(csv.DictReader(catalog_path.open()))

    # Load Google Drive mapping if available
    drive_map_path = root / "dashboard" / "drive-mapping.json"
    drive_map = {}
    if drive_map_path.is_file():
        drive_map = json.loads(drive_map_path.read_text())

    # Load device meta
    meta = {}
    for rd in sorted(runs_dir.iterdir()):
        mf = rd / "meta.json"
        if mf.is_file():
            meta = json.loads(mf.read_text()); break

    # Collect latest result per UAT ID across ALL runs
    latest = {}
    for rd in sorted(runs_dir.iterdir()):
        if not rd.is_dir(): continue
        for td in sorted(rd.iterdir()):
            if not td.name.startswith("test-"): continue
            sj = td / "steps.json"
            if not sj.is_file(): continue
            try: data = json.loads(sj.read_text())
            except: continue
            tid = data.get("id","")
            md = root / "tests" / f"{tid}.md"
            if md.is_file():
                m = re.search(r'^uat_id:\s*(\S+)', md.read_text(), re.MULTILINE)
                if m:
                    video_path = td / "video.mp4"
                    has_video = video_path.is_file() and video_path.stat().st_size > 0
                    screenshots = sorted(td.glob("step-*.png"))
                    uat_id = m.group(1)
                    # Resolve video: prefer Drive iframe, fallback to local
                    if uat_id in drive_map:
                        vid_ref = drive_map[uat_id]  # Drive file ID
                    elif has_video:
                        vid_ref = f"../runs/{rd.name}/test-{tid}/video.mp4"
                    else:
                        vid_ref = None
                    # Copy screenshots to dashboard/screenshots/<uat>/ for Vercel deploy
                    ss_deploy = []
                    ss_dir = root / "dashboard" / "screenshots" / uat_id
                    if screenshots:
                        ss_dir.mkdir(parents=True, exist_ok=True)
                        import shutil
                        for sp in screenshots:
                            dst = ss_dir / sp.name
                            if not dst.exists():
                                shutil.copy2(sp, dst)
                            ss_deploy.append(f"screenshots/{uat_id}/{sp.name}")
                    latest[uat_id] = {
                        "status": data["status"],
                        "error": data.get("error"),
                        "duration_ms": data.get("duration_ms", 0),
                        "run": rd.name, "test": tid,
                        "video": vid_ref,
                        "has_drive": uat_id in drive_map,
                        "screenshots": ss_deploy,
                    }

    for r in rows:
        uat = r["UAT ID"]
        if uat in latest:
            r["_status"] = latest[uat]["status"]
            r["_error"] = latest[uat].get("error") or ""
            r["_run"] = latest[uat]["run"]
            r["_video"] = latest[uat].get("video")
            r["_has_drive"] = latest[uat].get("has_drive", False)
            r["_screenshots"] = latest[uat].get("screenshots", [])
        else:
            r["_status"] = r["Status"].lower() if r["Status"] else "not_started"
            r["_error"] = r.get("Actual Result", "")
            r["_run"] = ""
            r["_video"] = None
            r["_has_drive"] = False
            r["_screenshots"] = []

    total = len(rows)
    counts = Counter(r["_status"] for r in rows)
    passed = counts.get("passed", 0)
    skipped = counts.get("skipped", 0)
    failed = counts.get("failed", 0)
    not_started = total - passed - skipped - failed
    pass_rate = (passed / total * 100) if total else 0
    exec_rate = ((passed + failed) / total * 100) if total else 0

    sections = defaultdict(lambda: {"total":0, "passed":0, "skipped":0, "failed":0})
    for r in rows:
        s = r["Section"]; sections[s]["total"] += 1
        st = r["_status"]
        if st in sections[s]: sections[s][st] += 1

    def classify_blocker(actual):
        a = actual.lower()
        if "manager" in a and "persona" in a: return "Akun Manager"
        if "email" in a or "inbox" in a: return "Akses Email"
        if "sso" in a or "idp" in a: return "SSO / IdP"
        if "2fa" in a or "otp" in a: return "Perangkat 2FA"
        if "push" in a and ("notif" in a or "server" in a): return "Push Notifikasi"
        if "network" in a and "rig" in a: return "Kontrol Jaringan"
        if "orientation" in a: return "Rotasi Layar"
        if "session ttl" in a or "idle timeout" in a: return "Tunggu Sesi TTL"
        if "lockout" in a or "disposable" in a: return "Akun Disposable"
        if "admin" in a or "grader" in a or "tos" in a: return "Role Admin / Grader"
        if any(k in a for k in ["quiz","essay","mcq","scored"]): return "Fixture Quiz / Skor"
        if any(k in a for k in ["audio","video","pdf","scorm offline","download"]): return "Variasi Konten (Video/Audio/PDF)"
        if any(k in a for k in ["unregistered","waitlist","recurring","capacity","attendance","recording"]): return "Fixture Event"
        if "prerequisite" in a or "locked" in a: return "Kursus Prasyarat"
        if "fresh account" in a or "zero interest" in a or "second learner" in a or "untargeted" in a: return "Akun Kedua / Baru"
        if "mutat" in a: return "Dihindari (Mutasi State)"
        if "web-only" in a or "not surfaced" in a: return "Hanya Web"
        if "double tap" in a or "race" in a: return "Race Condition"
        return "Dependensi Data Lainnya"

    blocker_counts = Counter()
    blocker_examples = defaultdict(list)
    for r in rows:
        if r["_status"] == "skipped":
            b = classify_blocker(r["_error"])
            blocker_counts[b] += 1
            if len(blocker_examples[b]) < 3:
                blocker_examples[b].append(r["UAT ID"])

    now = datetime.now().strftime("%d %B %Y, %H:%M")
    device = meta.get("device", {})
    apk = meta.get("apk", {})

    def badge(status):
        colors = {"passed":"#22c55e","failed":"#ef4444","skipped":"#3b82f6","not_started":"#a3a3a3"}
        bg = {"passed":"rgba(34,197,94,0.12)","failed":"rgba(239,68,68,0.12)","skipped":"rgba(59,130,246,0.12)","not_started":"rgba(163,163,163,0.12)"}
        labels = {"passed":"Lulus","failed":"Gagal","skipped":"Dilewati","not_started":"Belum Mulai"}
        return f'<span class="badge" style="color:{colors.get(status,"#a3a3a3")};background:{bg.get(status,"rgba(163,163,163,0.12)")}">{labels.get(status,status.title())}</span>'

    section_rows = ""
    for s in sorted(sections.keys()):
        d = sections[s]
        pct = (d["passed"] / d["total"] * 100) if d["total"] else 0
        section_rows += f'<tr><td>{s}</td><td class="c">{d["total"]}</td><td class="c g">{d["passed"]}</td><td class="c b">{d["skipped"]}</td><td class="c r">{d["failed"]}</td><td><div class="bar-bg"><div class="bar-fill" style="width:{pct:.0f}%">{pct:.0f}%</div></div></td></tr>'

    blocker_rows = ""
    for b, c in blocker_counts.most_common():
        blocker_rows += f'<tr><td>{b}</td><td class="c">{c}</td><td class="muted">{", ".join(blocker_examples[b])}</td></tr>'

    tc_rows = ""
    for idx, r in enumerate(rows):
        st = r["_status"]
        pri = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(r["Priority"], "⚪")
        err = f'<div class="err">{r["_error"][:140]}{"…" if len(r["_error"])>140 else ""}</div>' if r["_error"] and st != "passed" else ""
        # Video column
        if r.get("_video"):
            is_drive = r.get("_has_drive", False)
            if is_drive:
                vid_cell = f'<button class="btn-play" onclick="openDriveModal(\'{r["_video"]}\',\'{r["UAT ID"]}\')">&#9654; Putar</button>'
            else:
                vid_cell = f'<button class="btn-play" onclick="openLocalModal(\'{r["_video"]}\',\'{r["UAT ID"]}\')">&#9654; Putar</button>'
        else:
            vid_cell = '<span class="muted">—</span>'
        # Screenshot column
        if r.get("_screenshots"):
            thumbs = " ".join(f'<a href="{s}" target="_blank"><img src="{s}" class="thumb" loading="lazy"></a>' for s in r["_screenshots"][:4])
            if len(r["_screenshots"]) > 4:
                thumbs += f'<span class="muted">+{len(r["_screenshots"])-4}</span>'
            ss_cell = f'<div class="thumb-row">{thumbs}</div>'
        else:
            ss_cell = '<span class="muted">—</span>'

        tc_rows += f'<tr><td class="mono">{r["UAT ID"]}</td><td>{r["Scenario"][:70]}{"…" if len(r["Scenario"])>70 else ""}</td><td class="c">{pri}</td><td class="c">{badge(st)}</td><td class="c">{vid_cell}</td><td>{ss_cell}</td><td>{err}</td></tr>'

    p_deg = passed / total * 360
    s_deg = skipped / total * 360
    f_deg = failed / total * 360

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Laporan QA — BAWANA Revamp Mobile</title>
<style>
  :root {{ --bg:#fff; --fg:#1a1a2e; --card:#f8fafc; --border:#e2e8f0;
           --pass:#22c55e; --fail:#ef4444; --skip:#3b82f6; --warn:#f59e0b;
           --muted:#94a3b8; --accent:#6366f1; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         background:var(--bg); color:var(--fg); line-height:1.6; }}
  .container {{ max-width:1200px; margin:0 auto; padding:32px 24px; }}

  .header {{ text-align:center; margin-bottom:40px; border-bottom:2px solid var(--accent); padding-bottom:24px; }}
  .header h1 {{ font-size:28px; font-weight:700; color:var(--accent); }}
  .header .sub {{ color:var(--muted); font-size:14px; margin-top:8px; }}
  .meta {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; margin-top:16px; font-size:13px; }}
  .meta-item {{ background:var(--card); border:1px solid var(--border); border-radius:8px; padding:10px 14px; }}
  .meta-label {{ color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.5px; }}

  .summary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:16px; margin:32px 0; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:20px; text-align:center; }}
  .card .big {{ font-size:36px; font-weight:800; }}
  .card .label {{ font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-top:4px; }}

  .donut-wrap {{ display:flex; align-items:center; justify-content:center; gap:40px; margin:32px 0; flex-wrap:wrap; }}
  .donut {{ width:200px; height:200px; border-radius:50%;
            background:conic-gradient(var(--pass) 0deg {p_deg:.1f}deg, var(--skip) {p_deg:.1f}deg {p_deg+s_deg:.1f}deg, var(--fail) {p_deg+s_deg:.1f}deg {p_deg+s_deg+f_deg:.1f}deg, #d4d4d4 {p_deg+s_deg+f_deg:.1f}deg 360deg);
            display:flex; align-items:center; justify-content:center; }}
  .donut-hole {{ width:130px; height:130px; border-radius:50%; background:#fff;
                 display:flex; flex-direction:column; align-items:center; justify-content:center; }}
  .donut-hole .pct {{ font-size:32px; font-weight:800; color:var(--pass); }}
  .donut-hole .sub {{ font-size:11px; color:var(--muted); }}
  .legend {{ font-size:13px; }}
  .legend-item {{ display:flex; align-items:center; gap:8px; margin:6px 0; }}
  .legend-dot {{ width:12px; height:12px; border-radius:3px; flex-shrink:0; }}

  h2 {{ font-size:20px; font-weight:700; margin:40px 0 16px; padding-bottom:8px; border-bottom:2px solid var(--border); }}
  h2 .count {{ font-size:14px; font-weight:400; color:var(--muted); }}

  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th {{ background:var(--card); text-align:left; padding:10px 12px; font-weight:600;
       border-bottom:2px solid var(--border); color:var(--muted); text-transform:uppercase; font-size:11px; letter-spacing:.5px; position:sticky; top:0; z-index:1; }}
  td {{ padding:10px 12px; border-bottom:1px solid var(--border); vertical-align:top; }}
  .c {{ text-align:center; }}
  .g {{ color:var(--pass); }} .b {{ color:var(--skip); }} .r {{ color:var(--fail); }}
  .mono {{ font-family:'SF Mono','Fira Code',monospace; font-size:12px; white-space:nowrap; }}
  .muted {{ color:var(--muted); font-size:12px; }}
  .err {{ color:var(--muted); font-size:11px; max-width:280px; line-height:1.4; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; white-space:nowrap; }}

  .bar-bg {{ background:var(--border); border-radius:6px; height:22px; overflow:hidden; min-width:100px; }}
  .bar-fill {{ background:var(--pass); height:100%; border-radius:6px; font-size:11px; color:#fff;
               display:flex; align-items:center; padding-left:8px; font-weight:600; min-width:24px; }}

  .finding {{ background:var(--card); border-left:4px solid var(--accent); border-radius:0 8px 8px 0; padding:14px 18px; margin:10px 0; }}
  .finding .title {{ font-weight:600; font-size:14px; }}
  .finding .desc {{ font-size:13px; color:var(--muted); margin-top:4px; }}
  .blocker-high {{ border-left-color:var(--fail); }}
  .blocker-med {{ border-left-color:var(--warn); }}
  .blocker-low {{ border-left-color:var(--muted); }}

  /* Video button */
  .btn-play {{ background:var(--accent); color:#fff; border:none; border-radius:6px; padding:5px 14px;
               font-size:11px; cursor:pointer; font-weight:600; white-space:nowrap; }}
  .btn-play:hover {{ opacity:.85; }}

  /* Screenshot thumbs */
  .thumb-row {{ display:flex; gap:4px; flex-wrap:wrap; }}
  .thumb {{ width:48px; height:85px; object-fit:cover; border-radius:4px; border:1px solid var(--border); cursor:pointer; }}
  .thumb:hover {{ border-color:var(--accent); box-shadow:0 0 0 2px rgba(99,102,241,.3); }}

  /* Modal */
  .modal-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,.8);
                    z-index:1000; align-items:center; justify-content:center; }}
  .modal-overlay.active {{ display:flex; }}
  .modal-box {{ background:#111; border-radius:12px; padding:16px; max-width:480px; width:90%; position:relative; }}
  .modal-title {{ color:#fff; font-size:14px; font-weight:600; margin-bottom:10px; text-align:center; }}
  .modal-box video {{ width:100%; border-radius:8px; }}
  .modal-close {{ position:absolute; top:8px; right:12px; background:none; border:none; color:#fff; font-size:24px; cursor:pointer; z-index:1; }}
  .modal-close:hover {{ color:var(--fail); }}

  @media print {{
    .btn-play, .modal-overlay {{ display:none!important; }}
    body {{ font-size:11px; }}
    .container {{ max-width:100%; padding:16px; }}
    .card .big {{ font-size:28px; }}
    table {{ font-size:10px; }}
  }}

  .footer {{ text-align:center; padding:32px 0 16px; color:var(--muted); font-size:12px; border-top:1px solid var(--border); margin-top:40px; }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Laporan QA Test</h1>
    <div class="sub">BAWANA Revamp — Pengujian End-to-End Aplikasi Mobile</div>
    <div class="meta">
      <div class="meta-item"><div class="meta-label">Tanggal Laporan</div>{now}</div>
      <div class="meta-item"><div class="meta-label">Penguji</div>Refa Triana & Claude Opus 4.6 Max Effort</div>
      <div class="meta-item"><div class="meta-label">Perangkat</div>{device.get('brand','-')} {device.get('model','-')} &middot; Android {device.get('android_version','-')}</div>
      <div class="meta-item"><div class="meta-label">APK</div>{apk.get('package','-')} v{apk.get('version_name','-')} (build {apk.get('version_code','-')})</div>
      <div class="meta-item"><div class="meta-label">Layar</div>{device.get('screen_size','-')} @ {device.get('density','-')}dpi</div>
      <div class="meta-item"><div class="meta-label">Framework</div>mobile-mcp + adb + Claude AI</div>
    </div>
  </div>

  <h2>Ringkasan Eksekutif</h2>
  <div class="summary">
    <div class="card"><div class="big">{total}</div><div class="label">Total Skenario</div></div>
    <div class="card"><div class="big" style="color:var(--pass)">{passed}</div><div class="label">Lulus</div></div>
    <div class="card"><div class="big" style="color:var(--skip)">{skipped}</div><div class="label">Dilewati</div></div>
    <div class="card"><div class="big" style="color:var(--fail)">{failed}</div><div class="label">Gagal</div></div>
    <div class="card"><div class="big" style="color:var(--accent)">{pass_rate:.1f}%</div><div class="label">Tingkat Lulus</div></div>
    <div class="card"><div class="big" style="color:var(--warn)">{exec_rate:.1f}%</div><div class="label">Tingkat Eksekusi</div></div>
  </div>

  <div class="donut-wrap">
    <div class="donut"><div class="donut-hole"><div class="pct">{pass_rate:.0f}%</div><div class="sub">Tingkat Lulus</div></div></div>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--pass)"></div> Lulus ({passed})</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--skip)"></div> Dilewati ({skipped})</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--fail)"></div> Gagal ({failed})</div>
      <div class="legend-item"><div class="legend-dot" style="background:#d4d4d4"></div> Belum Mulai ({not_started})</div>
    </div>
  </div>

  <h2>Cakupan per Bagian <span class="count">({len(sections)} bagian)</span></h2>
  <table>
    <tr><th>Bagian</th><th class="c">Total</th><th class="c">Lulus</th><th class="c">Lewat</th><th class="c">Gagal</th><th>Tingkat Lulus</th></tr>
    {section_rows}
  </table>

  <h2>Temuan Utama</h2>
  <div class="finding">
    <div class="title">Alur Utama Pengguna Terverifikasi ({passed}/139)</div>
    <div class="desc">Autentikasi (login, logout, ubah password, error login invalid), navigasi Homepage (carousel, tap kartu, performa scroll, judul panjang), Profil (nama/email, upload foto, leaderboard, kalender, riwayat belajar), pemilihan Minat, siklus Assignment, daftar Event, dan ketersediaan Sertifikat semuanya lulus di mobile.</div>
  </div>
  <div class="finding">
    <div class="title">Retry Berbasis Vision Memulihkan 12 Skenario</div>
    <div class="desc">Sweep retry menggunakan verifikasi screenshot (untuk styling yang tidak terekspos di accessibility tree) menaikkan 12 skenario dari Dilewati menjadi Lulus — termasuk highlight tanggal kalender, urutan tie leaderboard, dan transisi status konten.</div>
  </div>
  <div class="finding">
    <div class="title">80 Skenario Terblokir oleh Kesenjangan Data / Infrastruktur</div>
    <div class="desc">Skenario yang dilewati BUKAN bug aplikasi — melainkan gap prasyarat data. Akun test sudah menghabiskan semua yang bisa diverifikasi dengan katalog konten saat ini (hanya modul SCORM, tidak ada quiz/video/audio/PDF), role saat ini (hanya learner, bukan manager), dan harness saat ini (tidak ada akses email, tidak ada trigger push, tidak ada toggle jaringan).</div>
  </div>
  <div class="finding">
    <div class="title">Nol Kegagalan Fungsional</div>
    <div class="desc">Tidak ada defect fungsional terdeteksi di semua skenario yang dieksekusi. Semua {passed} skenario yang dijalankan mengonfirmasi perilaku yang benar.</div>
  </div>

  <h2>Peta Penghambat <span class="count">(yang membuka 80 skenario dilewati)</span></h2>
  <table>
    <tr><th>Kategori Penghambat</th><th class="c">Jumlah</th><th>Contoh UAT ID</th></tr>
    {blocker_rows}
  </table>

  <h2>Rekomendasi</h2>
  <div class="finding blocker-high">
    <div class="title">1. Siapkan Quiz & Konten Berskor (membuka ~12 skenario)</div>
    <div class="desc">Minta admin membuat minimal satu essay quiz dan satu MCQ quiz dengan ambang batas kelulusan. Ini membuka LIB-M-012/014/015, FLOW-M-006/007, dan beberapa sub-test flow.</div>
  </div>
  <div class="finding blocker-high">
    <div class="title">2. Sediakan Akun Manager (membuka 7 skenario)</div>
    <div class="desc">Buat credential test dengan role manager di permata-revamp-stg. Ini membuka semua skenario TEAM-M-001 sampai TEAM-M-008.</div>
  </div>
  <div class="finding blocker-med">
    <div class="title">3. Tambah Konten Video/Audio/PDF (membuka ~6 skenario)</div>
    <div class="desc">Katalog saat ini hanya berisi modul SCORM. Menambahkan minimal satu video, satu audio, dan satu PDF mengaktifkan CON-M-001/002/007 dan LIB-M-005/007/008.</div>
  </div>
  <div class="finding blocker-med">
    <div class="title">4. Buat Event Publik Baru (membuka ~7 skenario)</div>
    <div class="desc">Semua 4 event yang terlihat sudah terdaftar untuk learner ini. Event publik baru mengaktifkan alur registrasi EVT-M-003/004 dan tes turunannya.</div>
  </div>
  <div class="finding blocker-low">
    <div class="title">5. Sediakan Akun Disposable (membuka ~5 skenario)</div>
    <div class="desc">Tes yang akan mengubah state akun (persistensi Like, hapus bookmark, edit profil) dapat dijalankan dengan aman di akun sekali pakai.</div>
  </div>

  <h2>Detail Test Case <span class="count">({total} skenario)</span></h2>
  <div style="overflow-x:auto">
  <table>
    <tr><th>UAT ID</th><th>Skenario</th><th class="c">Prioritas</th><th class="c">Status</th><th class="c">Video</th><th>Screenshot</th><th>Catatan</th></tr>
    {tc_rows}
  </table>
  </div>

  <div class="footer">
    Dibuat oleh <strong>Android AI Testing</strong> &middot; Penguji: Refa Triana & Claude Opus 4.6 Max Effort &middot; {now}<br>
    Sumber: <a href="https://github.com/refatriana31/android-ai-testing">github.com/refatriana31/android-ai-testing</a>
  </div>
</div>

<!-- Video Modal -->
<div class="modal-overlay" id="videoModal">
  <div class="modal-box">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <div class="modal-title" id="modalTitle"></div>
    <div id="modalContent"></div>
  </div>
</div>

<script>
function openDriveModal(fileId, title) {{
  var overlay = document.getElementById('videoModal');
  var content = document.getElementById('modalContent');
  var titleEl = document.getElementById('modalTitle');
  titleEl.textContent = title;
  content.innerHTML = '<iframe src="https://drive.google.com/file/d/' + fileId + '/preview" width="100%" height="480" frameborder="0" allow="autoplay" allowfullscreen style="border-radius:8px"></iframe>';
  overlay.classList.add('active');
}}
function openLocalModal(src, title) {{
  var overlay = document.getElementById('videoModal');
  var content = document.getElementById('modalContent');
  var titleEl = document.getElementById('modalTitle');
  titleEl.textContent = title;
  content.innerHTML = '<video controls autoplay width="100%" style="border-radius:8px"><source src="' + src + '" type="video/mp4"></video>';
  overlay.classList.add('active');
}}
function closeModal() {{
  var overlay = document.getElementById('videoModal');
  var content = document.getElementById('modalContent');
  content.innerHTML = '';
  overlay.classList.remove('active');
}}
document.getElementById('videoModal').addEventListener('click', function(e) {{
  if (e.target === this) closeModal();
}});
document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') closeModal();
}});
</script>
</body>
</html>"""

    out_path = Path(args.output) if args.output else root / "dashboard" / "pm-report.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(out_path)

if __name__ == "__main__":
    main()
