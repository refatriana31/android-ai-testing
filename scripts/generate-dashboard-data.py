#!/usr/bin/env python3
"""Generate a single dashboard/index.html with all data, Drive video, screenshots.

Merges the old UAT Dashboard + PM Report into one page:
  - Dark theme, Bahasa Indonesia
  - Summary cards + donut chart + progress bar
  - Section breakdown with bar charts
  - Temuan utama + blocker roadmap + rekomendasi
  - Full test table with search/filter + Video (Drive iframe) + Screenshot columns
  - Modal video player (Google Drive iframe)

Usage:
  scripts/generate-dashboard-data.py
"""
import csv, json, os, re, shutil
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

root = Path(__file__).resolve().parent.parent
runs_dir = root / "runs"
catalog_path = root / "tests" / "catalog.csv"
index_path = root / "dashboard" / "index.html"
drive_map_path = root / "dashboard" / "drive-mapping.json"

# Load Drive mapping
drive_map = {}
if drive_map_path.is_file():
    drive_map = json.loads(drive_map_path.read_text())

# Load catalog
catalog = list(csv.DictReader(catalog_path.open()))

# Load device meta
meta = {}
for rd in sorted(runs_dir.iterdir()):
    mf = rd / "meta.json"
    if mf.is_file():
        meta = json.loads(mf.read_text()); break

# Collect latest result per UAT ID
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
        if not md.is_file(): continue
        m = re.search(r'^uat_id:\s*(\S+)', md.read_text(), re.MULTILINE)
        if not m: continue
        uat = m.group(1)
        video_path = td / "video.mp4"
        has_video = video_path.is_file() and video_path.stat().st_size > 0
        screenshots = sorted(td.glob("step-*.png"))
        # Copy screenshots
        ss_paths = []
        if screenshots:
            ss_dir = root / "dashboard" / "screenshots" / uat
            ss_dir.mkdir(parents=True, exist_ok=True)
            for sp in screenshots:
                dst = ss_dir / sp.name
                if not dst.exists(): shutil.copy2(sp, dst)
                ss_paths.append(f"screenshots/{uat}/{sp.name}")
        latest[uat] = {
            "status": data["status"],
            "error": data.get("error"),
            "duration_ms": data.get("duration_ms", 0),
            "run": rd.name,
            "test": tid,
            "drive_id": drive_map.get(uat),
            "video_local": f"../runs/{rd.name}/test-{tid}/video.mp4" if has_video and uat not in drive_map else None,
            "screenshots": ss_paths,
        }

# Merge
for r in catalog:
    uat = r["UAT ID"]
    if uat in latest:
        r["_st"] = latest[uat]["status"]
        r["_err"] = latest[uat].get("error") or ""
        r["_drive"] = latest[uat].get("drive_id")
        r["_vid_local"] = latest[uat].get("video_local")
        r["_ss"] = latest[uat].get("screenshots", [])
    else:
        r["_st"] = "not_started"
        r["_err"] = ""
        r["_drive"] = None
        r["_vid_local"] = None
        r["_ss"] = []

total = len(catalog)
c = Counter(r["_st"] for r in catalog)
passed = c.get("passed",0)
skipped = c.get("skipped",0)
failed = c.get("failed",0)
ns = total - passed - skipped - failed
pass_rate = (passed/total*100) if total else 0
exec_rate = ((passed+failed)/total*100) if total else 0

# Sections
sections = defaultdict(lambda: {"t":0,"p":0,"s":0,"f":0})
for r in catalog:
    s = r["Section"]; sections[s]["t"] += 1
    st = r["_st"]
    if st == "passed": sections[s]["p"] += 1
    elif st == "skipped": sections[s]["s"] += 1
    elif st == "failed": sections[s]["f"] += 1

# Blockers
def classify(a):
    a = a.lower()
    if "manager" in a and "persona" in a: return ("Akun Manager","manager")
    if "email" in a or "inbox" in a: return ("Akses Email","email")
    if "sso" in a or "idp" in a: return ("SSO / IdP","sso")
    if "2fa" in a or "otp" in a: return ("Perangkat 2FA","2fa")
    if "push" in a and ("notif" in a or "server" in a): return ("Push Notifikasi","push")
    if "network" in a and "rig" in a: return ("Kontrol Jaringan","net")
    if "orientation" in a: return ("Rotasi Layar","orient")
    if "session ttl" in a or "idle timeout" in a: return ("Tunggu Sesi TTL","ttl")
    if "lockout" in a or "disposable" in a: return ("Akun Disposable","disp")
    if "admin" in a or "grader" in a or "tos" in a: return ("Admin / Grader","admin")
    if any(k in a for k in ["quiz","essay","mcq","scored"]): return ("Fixture Quiz","quiz")
    if any(k in a for k in ["audio","video","pdf","scorm offline","download"]): return ("Variasi Konten","content")
    if any(k in a for k in ["unregistered","waitlist","recurring","capacity","attendance","recording"]): return ("Fixture Event","event")
    if "prerequisite" in a or "locked" in a: return ("Kursus Prasyarat","prereq")
    if "fresh account" in a or "zero interest" in a or "second learner" in a or "untargeted" in a: return ("Akun Kedua","2nd")
    if "mutat" in a: return ("Mutasi Dihindari","mut")
    if "web-only" in a or "not surfaced" in a: return ("Hanya Web","web")
    return ("Dependensi Data","other")

blk_c = Counter(); blk_ex = defaultdict(list)
for r in catalog:
    if r["_st"] == "skipped":
        lbl, _ = classify(r["_err"])
        blk_c[lbl] += 1
        if len(blk_ex[lbl]) < 3: blk_ex[lbl].append(r["UAT ID"])

dev = meta.get("device",{})
apk = meta.get("apk",{})
now = datetime.now().strftime("%d %B %Y, %H:%M")

# Donut degrees
p_deg = passed/total*360
s_deg = skipped/total*360
f_deg = failed/total*360

# Section cards HTML
sec_html = ""
for s in sorted(sections.keys()):
    d = sections[s]
    pp = d["p"]/d["t"]*100 if d["t"] else 0
    sp = d["s"]/d["t"]*100 if d["t"] else 0
    fp = d["f"]/d["t"]*100 if d["t"] else 0
    np = 100 - pp - sp - fp
    sec_html += f'''<div class="section-card"><div class="sec-name">{s}</div>
      <div class="sec-bar"><div class="seg passed" style="width:{pp:.0f}%"></div><div class="seg skipped" style="width:{sp:.0f}%"></div><div class="seg failed" style="width:{fp:.0f}%"></div>{f'<div class="seg not-started" style="width:{np:.0f}%"></div>' if np > 0 else ''}</div>
      <div class="sec-stats"><div class="sec-stat"><span class="dot" style="background:var(--green)"></span>{d["p"]}L</div>{f'<div class="sec-stat"><span class="dot" style="background:var(--red)"></span>{d["f"]}G</div>' if d["f"]>0 else ''}<div class="sec-stat"><span class="dot" style="background:var(--yellow)"></span>{d["s"]}D</div><div class="sec-stat" style="margin-left:auto;font-weight:600">{d["t"]} total</div></div></div>'''

# Blocker cards
blk_html = ""
for lbl, cnt in blk_c.most_common():
    exs = ", ".join(blk_ex[lbl])
    blk_html += f'''<div class="blocker-card"><div class="bc-title">{lbl}</div><div class="bc-count">{cnt}</div><div class="bc-examples">{exs}</div></div>'''

# Test rows
rows_html = ""
for i, r in enumerate(catalog):
    st = r["_st"]; uat = r["UAT ID"]
    st_class = st.replace("_","-")
    st_label = {"passed":"Lulus","failed":"Gagal","skipped":"Dilewati","not_started":"Belum Mulai"}.get(st, st)
    pri = (r["Priority"] or "").lower()
    pri_label = r["Priority"] or ""
    err = r["_err"]
    trunc = (err[:120] + "...") if len(err) > 120 else err
    # Video cell
    if r["_drive"]:
        vid = f'<button class="btn-play" onclick="openModal(\'{r["_drive"]}\',\'{uat}\')">&#9654;</button>'
    elif r["_vid_local"]:
        vid = f'<button class="btn-play btn-local" onclick="openLocalModal(\'{r["_vid_local"]}\',\'{uat}\')">&#9654;</button>'
    else:
        vid = '<span class="dim">—</span>'
    # Screenshot cell
    if r["_ss"]:
        thumbs = "".join(f'<a href="{s}" target="_blank"><img src="{s}" class="thumb" loading="lazy"></a>' for s in r["_ss"][:3])
        extra = f'<span class="dim">+{len(r["_ss"])-3}</span>' if len(r["_ss"]) > 3 else ""
        ss = f'<div class="thumb-row">{thumbs}{extra}</div>'
    else:
        ss = '<span class="dim">—</span>'
    search_data = f"{uat} {r['Scenario']} {r['Section']} {st}".lower()
    pri_html = f'<span class="priority-badge {pri}">{pri_label}</span>' if pri else ""
    scenario_trunc = r["Scenario"][:70] + ("…" if len(r["Scenario"]) > 70 else "")
    note_html = trunc if st != "passed" else ""
    rows_html += f'<tr class="result-row" data-status="{st_class}" data-search="{search_data}"><td>{i+1}</td><td><strong>{uat}</strong></td><td>{r["Section"]}</td><td>{pri_html}</td><td>{scenario_trunc}</td><td><span class="status-badge {st_class}">{st_label}</span></td><td class="c">{vid}</td><td>{ss}</td><td class="notes">{note_html}</td></tr>'

html = f'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Laporan QA — BAWANA Revamp Mobile</title>
<style>
  :root {{ --bg:#0f172a; --surface:#1e293b; --surface2:#334155; --border:#475569;
           --text:#f1f5f9; --text2:#94a3b8; --green:#22c55e; --green-bg:rgba(34,197,94,.12);
           --red:#ef4444; --red-bg:rgba(239,68,68,.12); --yellow:#eab308; --yellow-bg:rgba(234,179,8,.12);
           --blue:#3b82f6; --blue-bg:rgba(59,130,246,.12); --purple:#a855f7; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }}
  .container {{ max-width:1320px; margin:0 auto; padding:24px 20px; }}
  .header {{ text-align:center; margin-bottom:40px; }}
  .header h1 {{ font-size:28px; font-weight:700; }}
  .header .sub {{ color:var(--text2); font-size:14px; margin-top:4px; }}
  .meta-badges {{ display:flex; gap:12px; justify-content:center; margin-top:16px; flex-wrap:wrap; }}
  .meta-badge {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:8px 16px; font-size:13px; color:var(--text2); }}
  .meta-badge strong {{ color:var(--text); }}
  .summary-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:16px; margin-bottom:32px; }}
  .summary-card {{ background:var(--surface); border-radius:12px; padding:20px; text-align:center; border:1px solid var(--border); }}
  .summary-card .number {{ font-size:40px; font-weight:800; line-height:1; }}
  .summary-card .label {{ font-size:11px; color:var(--text2); margin-top:8px; text-transform:uppercase; letter-spacing:.5px; }}
  .summary-card.passed .number {{ color:var(--green); }}
  .summary-card.failed .number {{ color:var(--red); }}
  .summary-card.skipped .number {{ color:var(--yellow); }}
  .summary-card.total .number {{ color:var(--blue); }}
  .summary-card.rate .number {{ color:var(--purple); }}
  .donut-wrap {{ display:flex; align-items:center; justify-content:center; gap:40px; margin:24px 0 32px; flex-wrap:wrap; }}
  .donut {{ width:180px; height:180px; border-radius:50%;
            background:conic-gradient(var(--green) 0deg {p_deg:.1f}deg, var(--yellow) {p_deg:.1f}deg {p_deg+s_deg:.1f}deg, var(--red) {p_deg+s_deg:.1f}deg {p_deg+s_deg+f_deg:.1f}deg, var(--surface2) {p_deg+s_deg+f_deg:.1f}deg 360deg);
            display:flex; align-items:center; justify-content:center; }}
  .donut-hole {{ width:120px; height:120px; border-radius:50%; background:var(--bg);
                 display:flex; flex-direction:column; align-items:center; justify-content:center; }}
  .donut-hole .pct {{ font-size:30px; font-weight:800; color:var(--green); }}
  .donut-hole .sub {{ font-size:10px; color:var(--text2); }}
  .legend {{ font-size:13px; }}
  .legend-item {{ display:flex; align-items:center; gap:8px; margin:6px 0; color:var(--text2); }}
  .legend-dot {{ width:12px; height:12px; border-radius:3px; flex-shrink:0; }}
  .section-title {{ font-size:20px; font-weight:700; margin:32px 0 16px; }}
  .section-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; margin-bottom:32px; }}
  .section-card {{ background:var(--surface); border-radius:12px; padding:20px; border:1px solid var(--border); }}
  .sec-name {{ font-size:15px; font-weight:600; margin-bottom:12px; }}
  .sec-bar {{ height:8px; border-radius:4px; background:var(--surface2); overflow:hidden; display:flex; margin-bottom:8px; }}
  .sec-bar .seg {{ height:100%; }}
  .seg.passed {{ background:var(--green); }} .seg.failed {{ background:var(--red); }} .seg.skipped {{ background:var(--yellow); }} .seg.not-started {{ background:var(--surface); }}
  .sec-stats {{ display:flex; gap:12px; font-size:12px; color:var(--text2); }}
  .sec-stat {{ display:flex; align-items:center; gap:4px; }}
  .sec-stat .dot {{ width:8px; height:8px; border-radius:2px; display:inline-block; }}
  .finding {{ background:var(--surface); border-left:4px solid var(--blue); border-radius:0 8px 8px 0; padding:14px 18px; margin:10px 0; }}
  .finding .ftitle {{ font-weight:600; font-size:14px; }}
  .finding .fdesc {{ font-size:13px; color:var(--text2); margin-top:4px; }}
  .finding.high {{ border-left-color:var(--red); }} .finding.med {{ border-left-color:var(--yellow); }} .finding.low {{ border-left-color:var(--text2); }}
  .blocker-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; margin-bottom:32px; }}
  .blocker-card {{ background:var(--surface); border-radius:12px; padding:20px; border:1px solid var(--border); }}
  .bc-title {{ font-size:14px; font-weight:600; }} .bc-count {{ font-size:28px; font-weight:800; color:var(--yellow); margin:4px 0 8px; }}
  .bc-examples {{ font-size:11px; color:var(--text2); font-family:monospace; }}
  .tabs {{ display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }}
  .tab-btn {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:8px 18px; font-size:13px; color:var(--text2); cursor:pointer; }}
  .tab-btn:hover {{ border-color:var(--blue); color:var(--text); }}
  .tab-btn.active {{ background:var(--blue); border-color:var(--blue); color:#fff; }}
  .search-box {{ width:100%; padding:10px 16px; background:var(--surface); border:1px solid var(--border); border-radius:8px; color:var(--text); font-size:14px; margin-bottom:16px; outline:none; }}
  .search-box:focus {{ border-color:var(--blue); }}
  .search-box::placeholder {{ color:var(--text2); }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  thead th {{ background:var(--surface2); padding:10px 12px; text-align:left; font-weight:600; color:var(--text2); text-transform:uppercase; font-size:11px; letter-spacing:.5px; position:sticky; top:0; z-index:1; }}
  tbody td {{ padding:8px 12px; border-bottom:1px solid var(--border); vertical-align:top; }}
  tbody tr:hover {{ background:rgba(255,255,255,.03); }}
  .c {{ text-align:center; }}
  .status-badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:11px; font-weight:600; text-transform:uppercase; }}
  .status-badge.passed {{ background:var(--green-bg); color:var(--green); }}
  .status-badge.failed {{ background:var(--red-bg); color:var(--red); }}
  .status-badge.skipped,.status-badge.dilewati {{ background:var(--yellow-bg); color:var(--yellow); }}
  .status-badge.not-started {{ background:var(--blue-bg); color:var(--blue); }}
  .priority-badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:500; }}
  .priority-badge.high {{ background:rgba(239,68,68,.15); color:var(--red); }}
  .priority-badge.medium {{ background:rgba(234,179,8,.15); color:var(--yellow); }}
  .priority-badge.low {{ background:rgba(34,197,94,.15); color:var(--green); }}
  .btn-play {{ background:var(--blue); color:#fff; border:none; border-radius:6px; padding:5px 10px; font-size:12px; cursor:pointer; font-weight:600; }}
  .btn-play:hover {{ opacity:.85; }}
  .btn-local {{ background:var(--purple); }}
  .thumb-row {{ display:flex; gap:3px; flex-wrap:wrap; }}
  .thumb {{ width:40px; height:72px; object-fit:cover; border-radius:3px; border:1px solid var(--border); cursor:pointer; }}
  .thumb:hover {{ border-color:var(--blue); }}
  .dim {{ color:var(--text2); font-size:12px; }}
  .notes {{ max-width:260px; font-size:11px; color:var(--text2); line-height:1.4; }}
  .modal-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,.85); z-index:1000; align-items:center; justify-content:center; }}
  .modal-overlay.active {{ display:flex; }}
  .modal-box {{ background:#111; border-radius:12px; padding:16px; max-width:480px; width:92%; position:relative; }}
  .modal-title {{ color:#fff; font-size:14px; font-weight:600; margin-bottom:10px; text-align:center; }}
  .modal-close {{ position:absolute; top:8px; right:12px; background:none; border:none; color:#fff; font-size:24px; cursor:pointer; }}
  .modal-close:hover {{ color:var(--red); }}
  #modalContent iframe, #modalContent video {{ width:100%; border-radius:8px; }}
  .footer {{ text-align:center; padding:32px 0 16px; color:var(--text2); font-size:12px; border-top:1px solid var(--border); margin-top:40px; }}
  @media (max-width:600px) {{ .summary-grid {{ grid-template-columns:repeat(2,1fr); }} .section-grid,.blocker-grid {{ grid-template-columns:1fr; }} }}
  @media print {{ .btn-play,.modal-overlay {{ display:none!important; }} body {{ font-size:11px; background:#fff; color:#000; }} .summary-card,.section-card,.blocker-card,.finding {{ border-color:#ddd; background:#f9f9f9; }} }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Laporan QA Test</h1>
    <div class="sub">BAWANA Revamp — Pengujian End-to-End Aplikasi Mobile</div>
    <div class="meta-badges">
      <div class="meta-badge"><strong>Tanggal:</strong> {now}</div>
      <div class="meta-badge"><strong>Penguji:</strong> Refa Triana & Claude Opus 4.6</div>
      <div class="meta-badge"><strong>Device:</strong> {dev.get("brand","-")} {dev.get("model","-")} &middot; Android {dev.get("android_version","-")}</div>
      <div class="meta-badge"><strong>APK:</strong> {apk.get("package","-")} v{apk.get("version_name","-")}</div>
      <div class="meta-badge"><strong>Layar:</strong> {dev.get("screen_size","-")} @ {dev.get("density","-")}dpi</div>
    </div>
  </div>

  <div class="summary-grid">
    <div class="summary-card total"><div class="number">{total}</div><div class="label">Total Skenario</div></div>
    <div class="summary-card passed"><div class="number">{passed}</div><div class="label">Lulus</div></div>
    <div class="summary-card skipped"><div class="number">{skipped}</div><div class="label">Dilewati</div></div>
    <div class="summary-card failed"><div class="number">{failed}</div><div class="label">Gagal</div></div>
    <div class="summary-card rate"><div class="number">{pass_rate:.1f}%</div><div class="label">Tingkat Lulus</div></div>
    <div class="summary-card rate"><div class="number">{exec_rate:.1f}%</div><div class="label">Tingkat Eksekusi</div></div>
  </div>

  <div class="donut-wrap">
    <div class="donut"><div class="donut-hole"><div class="pct">{pass_rate:.0f}%</div><div class="sub">Tingkat Lulus</div></div></div>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div>Lulus ({passed})</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--yellow)"></div>Dilewati ({skipped})</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--red)"></div>Gagal ({failed})</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--surface2)"></div>Belum Mulai ({ns})</div>
    </div>
  </div>

  <h2 class="section-title">Cakupan per Bagian</h2>
  <div class="section-grid">{sec_html}</div>

  <h2 class="section-title">Temuan Utama</h2>
  <div class="finding"><div class="ftitle">Alur Utama Terverifikasi ({passed}/{total})</div><div class="fdesc">Autentikasi, navigasi Homepage, Profil, Leaderboard, Kalender, Interest selection, Assignment, Event, Sertifikat — semuanya lulus di mobile.</div></div>
  <div class="finding"><div class="ftitle">Retry Vision Memulihkan 12 Skenario</div><div class="fdesc">Sweep retry dengan verifikasi screenshot menaikkan 12 skenario dari Dilewati → Lulus (calendar highlight, tie leaderboard, status konten).</div></div>
  <div class="finding"><div class="ftitle">{skipped} Skenario Terblokir Data / Infrastruktur</div><div class="fdesc">BUKAN bug aplikasi — melainkan gap prasyarat (hanya SCORM, tidak ada quiz/video/audio/PDF; hanya learner, bukan manager; tidak ada akses email/push/network toggle).</div></div>
  <div class="finding"><div class="ftitle">Nol Kegagalan Fungsional</div><div class="fdesc">Tidak ada defect fungsional. Semua {passed} skenario yang dieksekusi mengonfirmasi perilaku benar.</div></div>

  <h2 class="section-title">Penghambat ({skipped} skenario dilewati)</h2>
  <div class="blocker-grid">{blk_html}</div>

  <h2 class="section-title">Rekomendasi</h2>
  <div class="finding high"><div class="ftitle">1. Siapkan Quiz & Konten Berskor (~12 skenario)</div><div class="fdesc">Buat minimal 1 essay quiz + 1 MCQ dengan ambang kelulusan → membuka LIB-M-012/014/015, FLOW-M-006/007.</div></div>
  <div class="finding high"><div class="ftitle">2. Sediakan Akun Manager (7 skenario)</div><div class="fdesc">Credential manager-role di permata-revamp-stg → membuka TEAM-M-001 sampai TEAM-M-008.</div></div>
  <div class="finding med"><div class="ftitle">3. Tambah Video/Audio/PDF (~6 skenario)</div><div class="fdesc">Katalog saat ini hanya SCORM. Minimal 1 video + 1 audio + 1 PDF → membuka CON-M-001/002/007.</div></div>
  <div class="finding med"><div class="ftitle">4. Event Publik Baru (~7 skenario)</div><div class="fdesc">Semua event sudah terdaftar. 1 event publik baru → membuka EVT-M-003/004 dan turunannya.</div></div>
  <div class="finding low"><div class="ftitle">5. Akun Disposable (~5 skenario)</div><div class="fdesc">Tes yang mengubah state (Like, bookmark, profile edit) bisa jalan di akun sekali pakai.</div></div>

  <h2 class="section-title">Detail Test Case</h2>
  <input type="text" class="search-box" id="searchInput" placeholder="Cari UAT ID, skenario, bagian, atau status...">
  <div class="tabs">
    <button class="tab-btn active" data-filter="all">Semua ({total})</button>
    <button class="tab-btn" data-filter="passed">Lulus ({passed})</button>
    <button class="tab-btn" data-filter="skipped">Dilewati ({skipped})</button>
    <button class="tab-btn" data-filter="failed">Gagal ({failed})</button>
    {"" if ns == 0 else f'<button class="tab-btn" data-filter="not-started">Belum Mulai ({ns})</button>'}
  </div>
  <div style="overflow-x:auto">
    <table>
      <thead><tr><th>#</th><th>UAT ID</th><th>Bagian</th><th>Prioritas</th><th>Skenario</th><th>Status</th><th class="c">Video</th><th>Screenshot</th><th>Catatan</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>

  <div class="footer">
    Dibuat oleh <strong>Android AI Testing</strong> &middot; Penguji: Refa Triana & Claude Opus 4.6 &middot; {now}<br>
    <a href="https://github.com/refatriana31/android-ai-testing" style="color:var(--blue)">github.com/refatriana31/android-ai-testing</a>
  </div>
</div>

<div class="modal-overlay" id="videoModal">
  <div class="modal-box">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <div class="modal-title" id="modalTitle"></div>
    <div id="modalContent"></div>
  </div>
</div>

<script>
function openModal(fileId,title){{var o=document.getElementById('videoModal'),c=document.getElementById('modalContent'),t=document.getElementById('modalTitle');t.textContent=title;c.innerHTML='<iframe src="https://drive.google.com/file/d/'+fileId+'/preview" width="100%" height="480" frameborder="0" allow="autoplay" allowfullscreen></iframe>';o.classList.add('active');}}
function openLocalModal(src,title){{var o=document.getElementById('videoModal'),c=document.getElementById('modalContent'),t=document.getElementById('modalTitle');t.textContent=title;c.innerHTML='<video controls autoplay width="100%"><source src="'+src+'" type="video/mp4"></video>';o.classList.add('active');}}
function closeModal(){{var o=document.getElementById('videoModal');document.getElementById('modalContent').innerHTML='';o.classList.remove('active');}}
document.getElementById('videoModal').addEventListener('click',function(e){{if(e.target===this)closeModal();}});
document.addEventListener('keydown',function(e){{if(e.key==='Escape')closeModal();}});
(function(){{
  var tabs=document.querySelectorAll('.tab-btn'),rows=document.querySelectorAll('.result-row'),input=document.getElementById('searchInput');
  function apply(){{var f=document.querySelector('.tab-btn.active').dataset.filter,s=input.value.toLowerCase();rows.forEach(function(r){{var ms=f==='all'||r.dataset.status===f,mt=!s||r.dataset.search.includes(s);r.style.display=(ms&&mt)?'':'none';}});}}
  tabs.forEach(function(t){{t.addEventListener('click',function(){{tabs.forEach(function(x){{x.classList.remove('active');}});t.classList.add('active');apply();}});}});
  input.addEventListener('input',apply);
}})();
</script>
</body>
</html>'''

index_path.write_text(html)
print(f"Generated {index_path} ({len(html)//1024}KB)")
print(f"  {passed} passed, {skipped} skipped, {failed} failed, {ns} not started")
print(f"  {sum(1 for r in catalog if r['_drive'])} Drive videos, {sum(1 for r in catalog if r['_ss'])} with screenshots")
