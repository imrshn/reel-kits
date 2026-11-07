"""Build the small sound pack in sounds/ (all made from scratch here, free to use).

The renderer puts one of these on every cut and pop:
  cut   soft click with a little low body      (scene changes)
  pop   round bubble pop                       (items appearing)
  tick  short bright UI tick                   (highlights, buttons)
  ding  two-note chime                         (results, the comment being sent)
  type  a few soft key taps                    (typing)
  boom  warm low hit                           (the first frame and dark/light flips)

Usage:  python tools/make_sounds.py      (only needed if you deleted sounds/)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SOUNDS, write_wav  # noqa: E402

SR = 48000
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(d, a=0.002, decay=8.0):
    x = t(d)
    return np.minimum(1, x / a) * np.exp(-x * decay)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def stereo(x, width=0.25, delay_ms=0.6):
    d = int(SR * delay_ms / 1000)
    l = x
    r = np.concatenate([np.zeros(d), x[:-d]]) if d else x
    m = (l + r) / 2
    s = (l - r) / 2 * (1 + width * 4)
    return np.stack([m + s, m - s], axis=1)


def norm(x, peak_db=-3.0):
    return x / (np.abs(x).max() + 1e-9) * 10 ** (peak_db / 20)


def cut():
    d = 0.22
    click = lowpass(rng.standard_normal(len(t(d))), 3500) * env(d, 0.0008, 90)
    body = np.sin(2 * np.pi * 150 * t(d) * (1 - 0.35 * t(d) / d)) * env(d, 0.002, 26) * 0.9
    return norm(click * 0.7 + body, -4)


def pop():
    d = 0.16
    f = 520 + 520 * np.exp(-t(d) * 40)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return norm(np.sin(ph) * env(d, 0.001, 30), -5)


def tick():
    d = 0.08
    x = np.sin(2 * np.pi * 1850 * t(d)) * env(d, 0.0005, 70) + 0.3 * np.sin(2 * np.pi * 3700 * t(d)) * env(d, 0.0005, 110)
    return norm(x, -8)


def ding():
    d = 0.9
    a = sum(np.sin(2 * np.pi * f * t(d)) * g for f, g in ((1046.5, 1), (2093, .25), (3139.5, .08))) * env(d, 0.003, 5)
    b = sum(np.sin(2 * np.pi * f * t(d)) * g for f, g in ((1568, 1), (3136, .22))) * env(d, 0.003, 4.5)
    off = int(SR * 0.09)
    b = np.concatenate([np.zeros(off), b[:-off]])
    return norm(a * 0.7 + b * 0.8, -7)


def typing():
    d = 0.5
    x = np.zeros(len(t(d)))
    for k, at in enumerate((0.0, 0.085, 0.16, 0.25, 0.33, 0.41)):
        dd = 0.03
        c = lowpass(rng.standard_normal(len(t(dd))), 2600 + 300 * (k % 3)) * env(dd, 0.0005, 160)
        i = int(at * SR)
        x[i:i + len(c)] += c * (0.7 + 0.3 * rng.random())
    return norm(x, -10)


def boom():
    d = 1.1
    f = 62 + 50 * np.exp(-t(d) * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env(d, 0.004, 3.6)
    air = lowpass(rng.standard_normal(len(t(d))), 900) * env(d, 0.002, 14) * 0.35
    return norm(body + air, -3)


def main() -> None:
    SOUNDS.mkdir(exist_ok=True)
    for name, fn in (("cut", cut), ("pop", pop), ("tick", tick), ("ding", ding), ("type", typing), ("boom", boom)):
        x = fn()
        fade = int(SR * 0.01)
        x[-fade:] *= np.linspace(1, 0, fade)
        write_wav(SOUNDS / f"{name}.wav", stereo(x), SR)
        print("made", name)


if __name__ == "__main__":
    main()
