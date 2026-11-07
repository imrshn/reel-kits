"""Shared helpers for the reel tools: folders, settings, FFmpeg and the browser."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent          # the "AI Video Editor" folder
ENGINE = ROOT / "engine"
REELS = ROOT / "reels"
EXPORTS = ROOT / "exports"
MODELS = ROOT / "models"
SOUNDS = ROOT / "sounds"
SETTINGS_FILE = ROOT / "settings.json"

KOKORO_MODEL = MODELS / "kokoro" / "kokoro-v1.0.int8.onnx"
KOKORO_VOICES = MODELS / "kokoro" / "voices-v1.0.bin"
ASR_DIR = MODELS / "parakeet"          # sherpa-onnx NeMo Parakeet TDT-CTC 110M (int8)

DEFAULT_SETTINGS = {
    "voice_engine": "kokoro",      # kokoro (free, on this computer) | fish | elevenlabs | file
    "kokoro_voice": "am_michael",  # try af_heart, af_bella, am_michael, am_puck, bf_emma, bm_george
    "speed": 1.12,                 # 1.0 = normal. Reels feel best a little fast.
    "sentence_pause": 0.16,        # seconds of silence between sentences (Kokoro)
    "keyword": "",                 # default comment keyword for the CTA scene
    "handle": "",                  # your Instagram handle, shown on covers if you want
    "music": "",                   # optional: a file in assets/music/ you have the rights to
    "music_db": -18,               # music level under the voice
    "fps": 30,
}


def say(msg: str) -> None:
    print(msg, flush=True)


def settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    if SETTINGS_FILE.exists():
        try:
            s.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
        except Exception as e:  # noqa: BLE001
            say(f"settings.json could not be read ({e}); using defaults.")
    return s


def load_env() -> None:
    """Read API keys from .env (KEY=value lines) without needing python-dotenv."""
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def reel_dir(name: str) -> Path:
    """Accept a slug ('airplane-food'), a folder path, or a path to a file inside it."""
    p = Path(name)
    if p.is_file():
        p = p.parent
    if not p.is_absolute() and not p.exists():
        p = REELS / name
    p = p.resolve()
    if not p.exists():
        sys.exit(f"Can't find the reel folder '{name}'. Reels live in {REELS}.")
    return p


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48].strip("-") or "reel"


def ffmpeg() -> str:
    """FFmpeg that ships inside the Python package, so nobody has to install it."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001
        return "ffmpeg"


def run(cmd: list[str], quiet: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "")[-1500:]
        raise RuntimeError(f"Command failed: {' '.join(map(str, cmd[:3]))} ...\n{tail}")
    if not quiet:
        say(r.stdout)
    return r


def read_audio(path: Path, sr: int = 24000):
    """Decode any audio file to mono float32 at `sr` using the bundled FFmpeg."""
    import numpy as np
    r = subprocess.run([ffmpeg(), "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"Could not read audio {path}: {r.stderr.decode()[-500:]}")
    return np.frombuffer(r.stdout, dtype=np.float32).copy(), sr


def write_wav(path: Path, samples, sr: int) -> None:
    import numpy as np
    import soundfile as sf
    a = np.asarray(samples, dtype=np.float32)
    sf.write(str(path), a, sr, subtype="PCM_16")


def launch_browser(p):
    """Start a headless browser: Playwright's Chromium, else Chrome, else Edge."""
    errors = []
    exe = os.environ.get("REEL_BROWSER")
    if exe:
        try:
            return p.chromium.launch(executable_path=exe)
        except Exception as e:  # noqa: BLE001
            errors.append(f"REEL_BROWSER: {e}")
    try:
        return p.chromium.launch()
    except Exception as e:  # noqa: BLE001
        errors.append(f"chromium: {str(e).splitlines()[0]}")
    for channel in ("chrome", "msedge"):
        try:
            return p.chromium.launch(channel=channel)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{channel}: {str(e).splitlines()[0]}")
    raise RuntimeError("No browser found for rendering. Run the setup again (it installs one).\n" + "\n".join(errors))


def open_player(p, folder: Path, scale: float = 1.0):
    """Open the reel in the player page and wait until it is ready. Returns (browser, page, timeline)."""
    browser = launch_browser(p)
    page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=scale)
    url = (ENGINE / "player.html").as_uri() + "?reel=" + quote(folder.as_uri() + "/", safe="")
    page.goto(url)
    page.wait_for_function("window.READY === true", timeout=60000)
    failed = page.evaluate("window.FAILED || null")
    if failed:
        browser.close()
        raise RuntimeError(f"The reel did not load: {failed}")
    tl = page.evaluate("window.TIMELINE")
    return browser, page, tl


def next_version(stem: str, ext: str = ".mp4") -> Path:
    EXPORTS.mkdir(exist_ok=True)
    v = 1
    while (EXPORTS / f"{stem}-v{v}{ext}").exists():
        v += 1
    return EXPORTS / f"{stem}-v{v}{ext}"
