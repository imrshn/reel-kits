#!/usr/bin/env python3
"""Checks every tool the Reel editor needs and prints a plain-English status list.
Run with the kit's Python:  .venv/bin/python tools/check.py   (Windows: .venv\\Scripts\\python tools\\check.py)
"""
import shutil
import subprocess
import sys

def version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return (out.stdout or out.stderr).strip().splitlines()[0] if out.returncode == 0 else None
    except Exception:
        return None


rows = []
py_ok = sys.version_info >= (3, 9)
rows.append(("OK " if py_ok else "MISSING", "Python", sys.version.split()[0]))
ok_all = py_ok

# FFmpeg: same rule as edit.py (system build if it can draw captions, else the bundled one)
sys.path.insert(0, __import__("os").path.dirname(__file__))
try:
    from edit import find_ffmpeg, _has_captions
    ff, _ = find_ffmpeg()
    libass = _has_captions(ff)
    src = "bundled" if "static_ffmpeg" in ff else "system"
    rows.append(("OK " if libass else "MISSING", "FFmpeg (cut + export)",
                 f"{src}: {(version([ff, '-version']) or '')[:40]}" + ("" if libass else " | built without captions support")))
    ok_all &= libass
except SystemExit:
    rows.append(("MISSING", "FFmpeg (cut + export)", "not found"))
    ok_all = False

try:
    import faster_whisper
    rows.append(("OK ", "Whisper (captions)", f"faster-whisper {faster_whisper.__version__}"))
except Exception:
    rows.append(("MISSING", "Whisper (captions)", "not installed"))
    ok_all = False

try:
    import yt_dlp
    rows.append(("OK ", "yt-dlp (grab references)", f"yt-dlp {yt_dlp.version.__version__}"))
except Exception:
    rows.append(("MISSING", "yt-dlp (grab references)", "not installed"))
    ok_all = False

node = shutil.which("node")
nv = version([node, "--version"]) if node else None
node_ok = bool(nv) and int(nv.lstrip("v").split(".")[0]) >= 22
rows.append(("OK " if node_ok else "optional", "Node.js 22+ (motion graphics)", nv or "not installed"))
root = __import__("pathlib").Path(__file__).resolve().parent.parent
for name, pkg in (("HyperFrames (motion graphics)", "hyperframes"), ("Remotion (motion graphics)", "remotion")):
    pj = root / "node_modules" / pkg / "package.json"
    v = __import__("json").loads(pj.read_text()).get("version") if pj.exists() else None
    rows.append(("OK " if v else "optional", name, f"{pkg} {v}" if v else "not installed (only needed for animated graphics)"))

print()
for status, name, detail in rows:
    print(f"  [{status:8}] {name:32} {detail}")
print()
print("READY: you can edit Reels now." if ok_all else "NOT READY: something required is missing (see above).")
sys.exit(0 if ok_all else 1)
