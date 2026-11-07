"""Check that everything the reel maker needs is installed. Ends with READY or a list of fixes.

Usage:  .venv/bin/python tools/check.py        (Windows: .venv\\Scripts\\python tools\\check.py)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ASR_DIR, KOKORO_MODEL, KOKORO_VOICES, ROOT, SOUNDS, ffmpeg  # noqa: E402

problems: list[str] = []


def ok(label: str) -> None:
    print(f"  ok   {label}", flush=True)


def bad(label: str, fix: str) -> None:
    print(f"  --   {label}", flush=True)
    problems.append(f"{label}: {fix}")


def main() -> None:
    print("Checking the reel maker...")
    if sys.version_info >= (3, 10):
        ok(f"Python {sys.version.split()[0]}")
    else:
        bad("Python 3.10+", "install a newer Python (see START HERE.md)")
    if ".venv" not in sys.executable:
        bad("private environment", "run the tools with .venv's Python (see CLAUDE.md)")
    for mod, label in (("kokoro_onnx", "voice engine"), ("sherpa_onnx", "word timing engine"), ("playwright", "frame renderer"),
                       ("imageio_ffmpeg", "FFmpeg"), ("numpy", "numpy"), ("soundfile", "audio files"), ("PIL", "images")):
        try:
            __import__(mod)
            ok(label)
        except Exception:  # noqa: BLE001
            bad(label, "run python tools/setup.py")
    try:
        r = subprocess.run([ffmpeg(), "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=30)
        ok("video encoder") if "libx264" in r.stdout else bad("video encoder", "reinstall: .venv python -m pip install --force-reinstall imageio-ffmpeg")
    except Exception:  # noqa: BLE001
        bad("FFmpeg", "run python tools/setup.py")
    ok("free voice") if KOKORO_MODEL.exists() and KOKORO_VOICES.exists() else bad("free voice", "run python tools/setup.py")
    ok("word timing model") if (ASR_DIR / "model.int8.onnx").exists() else bad("word timing model", "run python tools/setup.py")
    ok("sound effects") if (SOUNDS / "cut.wav").exists() else bad("sound effects", "run .venv python tools/make_sounds.py")
    try:
        from common import launch_browser
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = launch_browser(p)
            pg = b.new_page(viewport={"width": 1080, "height": 1920})
            pg.goto((ROOT / "engine" / "player.html").as_uri() + "?reel=" + quote((ROOT / "reels" / "airplane-food").as_uri() + "/", safe=""))
            pg.wait_for_function("window.READY === true", timeout=30000)
            failed = pg.evaluate("window.FAILED || null")
            b.close()
        ok("browser + animation engine") if not failed else bad("animation engine", failed)
    except Exception as e:  # noqa: BLE001
        bad("browser", f"run python tools/setup.py ({str(e).splitlines()[0][:120]})")
    print()
    if problems:
        print("NOT READY. To fix:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("READY")


if __name__ == "__main__":
    main()
