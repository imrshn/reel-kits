"""Time every word of the script to the voice:  voice.wav + script.md  ->  words.json + words.js

It listens to the voice with a small speech model that runs on this computer, then
matches what it heard to the script, so captions use your exact spelling and
*accent* marks but land on the real timing.

Usage:  python tools/timing.py airplane-food
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ASR_DIR, read_audio, reel_dir, say  # noqa: E402

SR = 16000


def script_words(folder: Path) -> list[dict]:
    words = []
    for line in (folder / "script.md").read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("<!--") or s.startswith(">"):
            continue
        # keep *accent* groups together so we can flag each word inside them
        for m in re.finditer(r"\*([^*]+)\*|(\S+)", s):
            if m.group(1):
                for w in m.group(1).split():
                    words.append({"w": w, "em": True})
                # punctuation stuck after the closing * belongs to the last word
            else:
                tok = m.group(2)
                if words and re.fullmatch(r"[.,!?;:]+", tok):
                    words[-1]["w"] += tok
                    continue
                words.append({"w": tok, "em": False})
    return words


NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
       "8": "eight", "9": "nine", "10": "ten"}


def key(w: str) -> str:
    k = re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))
    return NUM.get(k, k)


def recognise(audio: np.ndarray) -> list[tuple[str, float]]:
    """Return [(word, start_seconds)] heard in the audio."""
    model = ASR_DIR / "model.int8.onnx"
    if not model.exists():
        sys.exit("The timing model isn't downloaded yet. Run: python tools/setup.py")
    import sherpa_onnx
    rec = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(model=str(model), tokens=str(ASR_DIR / "tokens.txt"), num_threads=2)
    # split long audio at quiet moments, about every 20 s
    hop = int(SR * 0.02)
    n = len(audio) // hop
    rms = np.sqrt((audio[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12) if n else np.zeros(1)
    cuts, pos = [0], 0
    while pos + SR * 24 < len(audio):
        lo, hi = (pos + SR * 16) // hop, min(n - 1, (pos + SR * 24) // hop)
        q = lo + int(np.argmin(rms[lo:hi])) if hi > lo else hi
        pos = q * hop
        cuts.append(pos)
    cuts.append(len(audio))
    out = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        st = rec.create_stream()
        st.accept_waveform(SR, audio[a:b])
        rec.decode_stream(st)
        r = st.result
        off = a / SR
        cur, t0 = "", None
        for tok, ts in zip(r.tokens, r.timestamps):
            if tok.startswith(" ") or tok.startswith("▁") or cur == "":
                if cur.strip():
                    out.append((cur.strip(), t0))
                cur, t0 = tok.replace("▁", " "), off + ts
            else:
                cur += tok
        if cur.strip():
            out.append((cur.strip(), t0))
    return out


def voice_end_times(audio: np.ndarray, starts: list[float]) -> list[float]:
    """End of each word: where the sound drops before the next word starts."""
    hop = int(SR * 0.01)
    n = len(audio) // hop
    rms = np.sqrt((audio[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    thr = max(rms.max() * 0.04, 1e-4)
    ends = []
    for i, s in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else len(audio) / SR
        a, b = int(s / 0.01), int(nxt / 0.01)
        seg = rms[a:b]
        loud = np.where(seg > thr)[0]
        e = (a + loud[-1] + 1) * 0.01 if len(loud) else min(nxt, s + 0.25)
        ends.append(round(min(nxt, max(s + 0.08, e)), 3))
    return ends


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reel")
    args = ap.parse_args()
    folder = reel_dir(args.reel)
    if not (folder / "voice.wav").exists():
        sys.exit("No voice.wav yet. Run tools/voice.py first.")
    audio, _ = read_audio(folder / "voice.wav", SR)
    say("Listening to the voice to time every word...")
    heard = recognise(audio)
    words = script_words(folder)
    a = [key(w["w"]) for w in words]
    b = [key(w) for w, _ in heard]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    starts: list[float | None] = [None] * len(words)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            starts[blk.a + k] = heard[blk.b + k][1]
    matched = sum(s is not None for s in starts)
    # fill the gaps (numbers, names the model spelled differently) by spreading them evenly
    total = len(audio) / SR
    known = [(i, s) for i, s in enumerate(starts) if s is not None]
    if not known:
        sys.exit("Couldn't hear any of the script in voice.wav. Is it the right recording?")
    for i in range(len(words)):
        if starts[i] is not None:
            continue
        prev = max([k for k in known if k[0] < i], default=(-1, 0.1), key=lambda k: k[0])
        nxt = min([k for k in known if k[0] > i], default=(len(words), total - 0.2), key=lambda k: k[0])
        frac = (i - prev[0]) / (nxt[0] - prev[0])
        starts[i] = prev[1] + (nxt[1] - prev[1]) * frac
    starts = [float(s) for s in starts]
    for i in range(1, len(starts)):                       # keep them in order
        starts[i] = max(starts[i], starts[i - 1] + 0.04)
    ends = voice_end_times(audio, starts)
    out = [{"w": w["w"], "s": round(s, 3), "e": e, "em": w["em"]} for w, s, e in zip(words, starts, ends)]
    (folder / "words.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    (folder / "words.js").write_text("window.WORDS = " + json.dumps(out) + ";\n", encoding="utf-8")
    pct = matched / max(1, len(words)) * 100
    say(f"Timed {len(out)} words ({pct:.0f}% heard clearly, the rest placed between them). Saved words.json.")
    if pct < 70:
        say("Warning: a lot of words didn't match. Check that script.md is what the voice actually says.")


if __name__ == "__main__":
    main()
