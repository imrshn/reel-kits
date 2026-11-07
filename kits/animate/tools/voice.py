"""Make the voiceover for a reel: reels/<name>/script.md  ->  reels/<name>/voice.wav

Engines (set "voice_engine" in settings.json, or pass --engine):
  kokoro      free voice that runs on this computer (default, no account needed)
  fish        your Fish Audio voice  (needs FISH_API_KEY and FISH_VOICE_ID in .env)
  elevenlabs  your ElevenLabs voice  (needs ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in .env)
  file        your own recording:  voice.py <reel> --file path/to/recording.mp3

Usage:
  python tools/voice.py airplane-food
  python tools/voice.py airplane-food --voice af_heart --speed 1.1
  python tools/voice.py airplane-food --file ~/Desktop/my-take.m4a
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (KOKORO_MODEL, KOKORO_VOICES, load_env, read_audio, reel_dir, say,  # noqa: E402
                    settings, write_wav)

SR = 24000


def script_text(folder: Path) -> str:
    """The words to speak: script.md without comments, headings, tags or *accent* marks."""
    f = folder / "script.md"
    if not f.exists():
        sys.exit(f"No script.md in {folder}. Write the script first.")
    lines = []
    for line in f.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("<!--") or s.startswith(">"):
            continue
        lines.append(s)
    text = " ".join(lines)
    text = text.replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def trim_silence(a: np.ndarray, sr: int, keep: float = 0.06) -> np.ndarray:
    if not len(a):
        return a
    env = np.abs(a)
    thr = max(1e-4, env.max() * 0.02)
    idx = np.where(env > thr)[0]
    if not len(idx):
        return a
    s = max(0, idx[0] - int(keep * sr))
    e = min(len(a), idx[-1] + int(keep * sr))
    return a[s:e]


def tighten(a: np.ndarray, sr: int, max_gap: float = 0.38, keep_gap: float = 0.28) -> np.ndarray:
    """Shorten long silences in a recording (keeps natural short pauses)."""
    hop = int(sr * 0.01)
    n = len(a) // hop
    if n < 10:
        return a
    frames = a[: n * hop].reshape(n, hop)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    thr = max(rms.max() * 0.03, 1e-4)
    quiet = rms < thr
    out, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            gap = (j - i) * 0.01
            if gap > max_gap and i > 0 and j < n:
                keep = int(keep_gap / 0.01)
                out.append(frames[i:i + keep // 2].ravel())
                out.append(frames[j - keep // 2:j].ravel())
            else:
                out.append(frames[i:j].ravel())
            i = j
        else:
            out.append(frames[i].ravel())
            i += 1
    out.append(a[n * hop:])
    return np.concatenate(out)


def kokoro(text: str, voice: str, speed: float, pause: float) -> np.ndarray:
    if not KOKORO_MODEL.exists() or not KOKORO_VOICES.exists():
        sys.exit("The free voice isn't downloaded yet. Run: python tools/setup.py")
    from kokoro_onnx import Kokoro
    k = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    if voice not in k.get_voices():
        sys.exit(f"Unknown voice '{voice}'. Try one of: {', '.join(sorted(k.get_voices()))}")
    out = []
    gap = np.zeros(int(SR * pause), dtype=np.float32)
    for i, s in enumerate(sentences(text)):
        a, sr = k.create(s, voice=voice, speed=speed, lang="en-gb" if voice[:1] == "b" else "en-us")
        a = trim_silence(np.asarray(a, dtype=np.float32), sr, keep=0.04)
        out.append(a)
        out.append(gap)
        say(f"  voiced line {i + 1}: {s[:60]}")
    return np.concatenate(out[:-1]) if out else np.zeros(SR, dtype=np.float32)


def http_audio(url: str, headers: dict, body: dict, dest: Path) -> Path:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            dest.write_bytes(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="ignore")[:400]
        sys.exit(f"The voice service said no ({e.code}): {msg}")
    return dest


def fish(text: str, folder: Path) -> np.ndarray:
    key, ref = os.environ.get("FISH_API_KEY"), os.environ.get("FISH_VOICE_ID")
    if not key or not ref:
        sys.exit("Add FISH_API_KEY and FISH_VOICE_ID to the .env file first (see .env.example).")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if os.environ.get("FISH_MODEL"):
        headers["model"] = os.environ["FISH_MODEL"]
    raw = http_audio("https://api.fish.audio/v1/tts", headers,
                     {"text": text, "reference_id": ref, "format": "mp3"}, folder / "voice-raw.mp3")
    a, _ = read_audio(raw, SR)
    return tighten(a, SR)


def elevenlabs(text: str, folder: Path) -> np.ndarray:
    key, vid = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVENLABS_VOICE_ID")
    if not key or not vid:
        sys.exit("Add ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID to the .env file first (see .env.example).")
    raw = http_audio(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
                     {"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
                     {"text": text, "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")},
                     folder / "voice-raw.mp3")
    a, _ = read_audio(raw, SR)
    return tighten(a, SR)


def finish(a: np.ndarray) -> np.ndarray:
    a = trim_silence(a, SR, keep=0.08)
    peak = float(np.abs(a).max() or 1)
    a = a / peak * 0.89                      # about -1 dB peak; render.py sets final loudness
    lead = np.zeros(int(SR * 0.15), dtype=np.float32)
    return np.concatenate([lead, a.astype(np.float32)])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reel")
    ap.add_argument("--engine")
    ap.add_argument("--voice", help="Kokoro voice name, e.g. am_michael or af_heart")
    ap.add_argument("--speed", type=float)
    ap.add_argument("--file", help="use your own recording instead of a generated voice")
    ap.add_argument("--no-tighten", action="store_true", help="keep the recording's pauses as they are")
    args = ap.parse_args()

    load_env()
    st = settings()
    folder = reel_dir(args.reel)
    engine = "file" if args.file else (args.engine or st["voice_engine"])
    text = script_text(folder)
    say(f"Making the voiceover with {engine} ({len(text.split())} words)...")

    if engine == "kokoro":
        a = kokoro(text, args.voice or st["kokoro_voice"], args.speed or st["speed"], st["sentence_pause"])
    elif engine == "fish":
        a = fish(text, folder)
    elif engine == "elevenlabs":
        a = elevenlabs(text, folder)
    elif engine == "file":
        src = Path(args.file or "").expanduser()
        if not src.exists():
            sys.exit(f"Can't find the recording {src}")
        a, _ = read_audio(src, SR)
        if not args.no_tighten:
            a = tighten(a, SR)
    else:
        sys.exit(f"Unknown voice engine '{engine}'. Use kokoro, fish, elevenlabs or file.")

    a = finish(a)
    out = folder / "voice.wav"
    write_wav(out, a, SR)
    words = len(text.split())
    dur = len(a) / SR
    say(f"Saved {out.name}: {dur:.1f} s, {words / dur:.1f} words per second.")
    if words / dur < 2.6:
        say("Tip: that's a bit slow for a reel. Try a higher speed (1.1 to 1.2).")
    say("Next: python tools/timing.py " + folder.name)


if __name__ == "__main__":
    main()
