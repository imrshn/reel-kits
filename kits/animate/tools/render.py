"""Render a reel to a ready-to-post MP4 (1080x1920, 30 fps, -14 LUFS).

Draws every frame in a headless browser, adds a sound on every cut and pop,
mixes it under the voice, and saves exports/<reel>-vN.mp4 (never overwrites).

Usage:
  python tools/render.py airplane-food
  python tools/render.py airplane-food --draft      (half size, quick look)
  python tools/render.py airplane-food --no-sfx
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ROOT, SOUNDS, ffmpeg, next_version, open_player, read_audio, reel_dir, run, say,  # noqa: E402
                    settings, write_wav)

SR = 48000
# level of each sound in dB (the voice peaks near -1 dB)
LEVEL = {"cut": -17, "pop": -19, "tick": -21, "ding": -18, "type": -20, "boom": -14}


def load_sound(name: str) -> np.ndarray | None:
    f = SOUNDS / f"{name}.wav"
    if not f.exists():
        return None
    import soundfile as sf
    a, sr = sf.read(str(f), dtype="float32", always_2d=True)
    if sr != SR:
        idx = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
        a = np.stack([np.interp(idx, np.arange(len(a)), a[:, c]) for c in range(a.shape[1])], axis=1)
    if a.shape[1] == 1:
        a = np.repeat(a, 2, axis=1)
    return a.astype(np.float32)


def mix(folder: Path, tl: dict, st: dict, sfx: bool, out: Path) -> None:
    dur = tl["duration"]
    n = int(dur * SR) + SR
    bus = np.zeros((n, 2), dtype=np.float32)
    voice_f = folder / tl.get("voice", "voice.wav")
    v = np.zeros(n, dtype=np.float32)
    if voice_f.exists():
        a, _ = read_audio(voice_f, SR)
        v[: min(n, len(a))] = a[: n]
    else:
        say("No voice.wav found; rendering without a voice.")
    # a touch of room so the voice doesn't sound flat-mono
    room = np.zeros_like(v)
    for d_ms, g in ((11, .10), (17, .07), (29, .05)):
        d = int(SR * d_ms / 1000)
        room[d:] += v[:-d] * g
    bus[:, 0] += v + room * 1.0
    bus[:, 1] += v - room * 0.6
    if sfx:
        cache = {}
        last = {}
        pan = [-.25, .2, -.1, .3, 0]
        for i, e in enumerate(tl.get("events", [])):
            k = e["kind"]
            if k not in cache:
                cache[k] = load_sound(k)
            s = cache[k]
            if s is None:
                continue
            if e["t"] - last.get(k, -9) < 0.12:          # don't stack the same sound
                continue
            last[k] = e["t"]
            g = 10 ** (LEVEL.get(k, -20) / 20)
            p = pan[i % len(pan)]
            i0 = int(max(0, e["t"] - (0.02 if k != "boom" else 0.0)) * SR)
            seg = s[: max(0, min(len(s), n - i0))]
            bus[i0:i0 + len(seg), 0] += seg[:, 0] * g * (1 - p)
            bus[i0:i0 + len(seg), 1] += seg[:, 1] * g * (1 + p)
    music = st.get("music") or ""
    if music:
        mf = (ROOT / "assets" / "music" / music)
        if mf.exists():
            m, _ = read_audio(mf, SR)
            m = np.resize(m, n) if len(m) < n else m[:n]
            # duck under the voice
            hop = int(SR * 0.02)
            nv = n // hop
            vr = np.sqrt((v[: nv * hop].reshape(nv, hop) ** 2).mean(axis=1) + 1e-12)
            talk = np.convolve((vr > vr.max() * 0.05).astype(float), np.ones(15) / 15, mode="same")
            duck = np.repeat(1 - 0.5 * np.clip(talk, 0, 1), hop)
            duck = np.concatenate([duck, np.ones(n - len(duck))])
            g = 10 ** (st.get("music_db", -18) / 20)
            fade = np.minimum(1, np.arange(n) / (SR * 1.0)) * np.minimum(1, (n - np.arange(n)) / (SR * 2.0))
            bus[:, 0] += m * g * duck * fade
            bus[:, 1] += m * g * duck * fade
        else:
            say(f"Music file {mf} not found; skipping music.")
    # soft end
    end = int(dur * SR)
    fl = int(SR * 0.6)
    bus[end - fl:end] *= np.linspace(1, 0.0, fl)[:, None]
    bus[end:] = 0
    bus = bus[:end]
    peak = np.abs(bus).max() or 1
    bus = bus / max(1.0, peak / 0.95)
    tmp = folder / ".work" / "mix-raw.wav"
    tmp.parent.mkdir(exist_ok=True)
    write_wav(tmp, bus, SR)
    # two-pass loudness to -14 LUFS, peaks under -1 dB
    r = subprocess.run([ffmpeg(), "-hide_banner", "-i", str(tmp), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    try:
        m = json.loads(js)
        af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    except Exception:  # noqa: BLE001
        af = "loudnorm=I=-14:TP=-1.5:LRA=11"
    run([ffmpeg(), "-y", "-hide_banner", "-i", str(tmp), "-af", af, "-ar", str(SR), str(out)])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reel")
    ap.add_argument("--draft", action="store_true", help="half size, faster, for a quick look")
    ap.add_argument("--no-sfx", action="store_true")
    ap.add_argument("--out", help="output file (default exports/<reel>-vN.mp4)")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright
    st = settings()
    folder = reel_dir(args.reel)
    scale = 0.5 if args.draft else 1.0
    out = Path(args.out) if args.out else next_version(folder.name + ("-draft" if args.draft else ""))
    work = folder / ".work"
    work.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser, page, tl = open_player(p, folder, scale)
        for w in tl.get("warnings", []):
            say("Warning: " + w)
        fps = int(tl.get("fps") or st["fps"])
        dur = float(tl["duration"])
        frames = int(round(dur * fps))
        say(f"Rendering {dur:.1f} s ({frames} frames)...")
        audio = work / "mix.wav"
        mix(folder, tl, st, not args.no_sfx, audio)
        w, h = int(1080 * scale), int(1920 * scale)
        enc = subprocess.Popen([
            ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
            "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
            "-i", str(audio),
            "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium" if not args.draft else "veryfast", "-crf", "18" if not args.draft else "24",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
            stdin=subprocess.PIPE)
        t0 = time.time()
        for i in range(frames):
            page.evaluate(f"window.seek({i / fps:.5f})")
            enc.stdin.write(page.screenshot(type="jpeg", quality=92))
            if i and i % (fps * 5) == 0:
                el = time.time() - t0
                say(f"  {i / fps:.0f} s of {dur:.0f} s drawn ({el / i * (frames - i):.0f} s left)")
        enc.stdin.close()
        enc.wait()
        browser.close()
    if enc.returncode != 0 or not out.exists():
        sys.exit("The video encoder failed. Try again; if it repeats, see TROUBLESHOOTING.md.")
    (folder / ".work" / "timeline.json").write_text(json.dumps(tl, indent=1), encoding="utf-8")
    say(f"Done: {out}  ({dur:.1f} s)")


if __name__ == "__main__":
    main()
