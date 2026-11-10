"""One-command setup. Run it with your normal Python:

  Mac:      python3 tools/setup.py
  Windows:  python tools\\setup.py      (or: py tools\\setup.py)

What it does, all inside this folder (no password, nothing system-wide):
  1. makes a private Python environment in .venv
  2. installs the tools (voice, timing, renderer, bundled FFmpeg)
  3. downloads the free voice (~120 MB) and the word-timing model (~100 MB) into models/
  4. gets a browser for drawing frames (uses Chrome or Edge if you have one)
  5. runs tools/check.py, which ends with READY
It is safe to run again; finished steps are skipped.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
WIN = os.name == "nt"
VPY = VENV / ("Scripts/python.exe" if WIN else "bin/python")

DOWNLOADS = [
    ("free voice model", "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx",
     ROOT / "models" / "kokoro" / "kokoro-v1.0.int8.onnx", None),
    ("voice styles", "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
     ROOT / "models" / "kokoro" / "voices-v1.0.bin", None),
    ("word-timing model", "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet_tdt_ctc_110m-en-36000-int8.tar.bz2",
     ROOT / "models" / "parakeet" / "model.int8.onnx", "sherpa-onnx-nemo-parakeet_tdt_ctc_110m-en-36000-int8"),
]


def say(m: str) -> None:
    print(m, flush=True)


def stage1() -> None:
    if sys.version_info < (3, 10):
        sys.exit(f"Python 3.10 or newer is needed (this is {sys.version.split()[0]}). See START HERE.md, step 'Python'.")
    if not VPY.exists():
        say("Step 1/5: making a private Python environment in .venv ...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    else:
        say("Step 1/5: private environment already there.")
    say("Step 2/5: installing the tools (2 to 5 minutes the first time) ...")
    subprocess.check_call([str(VPY), "-m", "pip", "install", "--disable-pip-version-check", "-q", "--upgrade", "pip"])
    subprocess.check_call([str(VPY), "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r",
                           str(ROOT / "tools" / "requirements.txt")])
    os.execv(str(VPY), [str(VPY), str(Path(__file__).resolve()), "--stage2"])


def fetch(label: str, url: str, dest: Path, inner: str | None) -> None:
    if dest.exists() and dest.stat().st_size > 1000:
        say(f"  {label}: already downloaded.")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.parent / (Path(url).name + ".part")
    say(f"  downloading the {label} ...")
    with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got, last = 0, -1
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
            got += len(b)
            pct = int(got * 100 / total) if total else 0
            if total and pct // 20 != last:
                last = pct // 20
                say(f"    {pct}%")
    if inner:                                         # a .tar.bz2 with a folder inside
        with tarfile.open(tmp, "r:bz2") as t:
            for m in t.getmembers():
                if m.isfile() and Path(m.name).name in ("model.int8.onnx", "tokens.txt"):
                    m.name = Path(m.name).name
                    try:
                        t.extract(m, dest.parent, filter="data")
                    except TypeError:            # older Python without extraction filters
                        t.extract(m, dest.parent)
        tmp.unlink()
    else:
        tmp.replace(dest)


def browser_ok() -> bool:
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from common import launch_browser
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = launch_browser(p)
            b.close()
        return True
    except Exception:  # noqa: BLE001
        return False


def stage2() -> None:
    say("Step 3/5: downloading the free voice and the word-timing model ...")
    for d in DOWNLOADS:
        fetch(*d)
    say("Step 4/5: checking for a browser to draw the frames ...")
    if browser_ok():
        say("  found one.")
    else:
        say("  installing a private copy of Chromium (about 150 MB) ...")
        subprocess.call([sys.executable, "-m", "playwright", "install", "chromium"])
    if not (ROOT / "sounds" / "cut.wav").exists():
        subprocess.call([sys.executable, str(ROOT / "tools" / "make_sounds.py")])
    if not (ROOT / "settings.json").exists() and (ROOT / "settings.example.json").exists():
        shutil.copy(ROOT / "settings.example.json", ROOT / "settings.json")
    say("Step 5/5: testing everything ...")
    r = subprocess.call([sys.executable, str(ROOT / "tools" / "check.py")])
    sys.exit(r)


if __name__ == "__main__":
    if "--stage2" in sys.argv:
        stage2()
    else:
        stage1()
