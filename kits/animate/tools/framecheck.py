"""Check a reel's frames before anyone sees it.

Looks at the reel every half second and reports:
  - text that leaves the screen, runs into the caption area or the Instagram buttons
  - text sitting on top of other text
  - moments where the picture doesn't change for too long (boring) or a scene drags
  - blank frames, missing images, words in scenes.js that the voice never says
It also saves pictures to look at yourself:
  reels/<name>/check/contact-sheet.jpg   one frame per scene, settled
  reels/<name>/check/scene-NN.jpg        each scene at full size
  reels/<name>/check/motion-NN.jpg       each scene as a strip of 4 moments (does it move well?)

Usage:  python tools/framecheck.py airplane-food
Exit code 0 = PASS, 1 = something to fix (listed in check/report.md).
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import open_player, reel_dir, say  # noqa: E402

AUDIT_JS = r"""
(() => {
  const out = [];
  const vis = el => {
    for (let n = el; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.05) return false;
    }
    return true;
  };
  document.querySelectorAll('[data-ai]').forEach(n => n.removeAttribute('data-ai'));
  const roots = [...document.querySelectorAll('#scenes .scene'), document.getElementById('cap')];
  roots.forEach(root => {
    if (!vis(root)) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
    for (let n = walker.currentNode; n; n = walker.nextNode()) {
      const own = [...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim());
      if (!own || !vis(n)) continue;
      const r = n.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      n.dataset.ai = out.length;
      const par = n.parentElement && n.parentElement.closest('[data-ai]');
      out.push({ id: out.length, parent: par ? +par.dataset.ai : -1, text: n.textContent.trim().slice(0, 40), x: r.left, y: r.top, w: r.width, h: r.height,
                 cap: root.id === 'cap', clip: n.scrollWidth > n.clientWidth + 2 && getComputedStyle(n).overflow === 'hidden' });
    }
  });
  return out;
})()
"""


def overlap(a, b):
    x = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    y = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return x * y / max(1, min(a["w"] * a["h"], b["w"] * b["h"]))


def inside(a, b):
    return a["x"] >= b["x"] - 1 and a["y"] >= b["y"] - 1 and a["x"] + a["w"] <= b["x"] + b["w"] + 1 and a["y"] + a["h"] <= b["y"] + b["h"] + 1


def related(boxes, a, b):
    def chain(x):
        seen = set()
        while x["parent"] >= 0 and x["parent"] not in seen:
            seen.add(x["parent"])
            x = boxes[x["parent"]]
        return seen
    return a["id"] in chain(b) or b["id"] in chain(a)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reel")
    ap.add_argument("--step", type=float, default=0.5)
    args = ap.parse_args()
    from PIL import Image, ImageDraw
    from playwright.sync_api import sync_playwright

    folder = reel_dir(args.reel)
    chk = folder / "check"
    chk.mkdir(exist_ok=True)
    for f in chk.glob("*.jpg"):
        f.unlink()
    issues: list[str] = []
    notes: list[str] = []

    with sync_playwright() as p:
        browser, page, tl = open_player(p, folder, 1.0)
        for w in tl.get("warnings", []):
            issues.append(f"Engine: {w}")
        dur = tl["duration"]
        scenes = tl["scenes"]

        # 1. layout audit on settled moments of every scene
        for si, s in enumerate(scenes):
            a, b = s["start"], s["end"]
            length = b - a
            if length > 6.5:
                issues.append(f"Scene {si + 1} ({s['type']}) holds for {length:.1f} s. Split it or add a change every 2 to 4 s.")
            if length < 0.8 and si < len(scenes) - 1:
                issues.append(f"Scene {si + 1} ({s['type']}) is only {length:.1f} s long; it will flash by.")
            ts = sorted({round(min(b - .3, a + x), 2) for x in (1.0, length / 2, length - .35) if a + x < b - .25 and x > .6})
            for t in ts:
                page.evaluate(f"window.seek({t})")
                boxes = page.evaluate(AUDIT_JS)
                where = f"{t:.1f} s (scene {si + 1}, {s['type']})"
                for bx in boxes:
                    if bx["x"] < 30 or bx["x"] + bx["w"] > 1050 or bx["y"] < 0 or bx["y"] + bx["h"] > 1920:
                        issues.append(f"{where}: \"{bx['text']}\" goes off the screen.")
                    elif not bx["cap"] and bx["y"] + bx["h"] > 1370:
                        issues.append(f"{where}: \"{bx['text']}\" runs into the caption area (bottom of content must stay above 1370 px).")
                    elif not bx["cap"] and bx["y"] < 250:
                        issues.append(f"{where}: \"{bx['text']}\" sits too high; Instagram covers the top 250 px.")
                    if bx["cap"] and bx["y"] + bx["h"] > 1560:
                        issues.append(f"{where}: the caption \"{bx['text']}\" drops into Instagram's button area. Use fewer words.")
                    if bx["clip"]:
                        issues.append(f"{where}: \"{bx['text']}\" is cut off.")
                for i in range(len(boxes)):
                    for j in range(i + 1, len(boxes)):
                        A, B = boxes[i], boxes[j]
                        if inside(A, B) or inside(B, A) or related(boxes, A, B):
                            continue
                        if overlap(A, B) > 0.18:
                            issues.append(f"{where}: \"{A['text']}\" overlaps \"{B['text']}\".")

        # 2. pictures: one settled frame per scene + 4-moment motion strips
        thumbs = []
        for si, s in enumerate(scenes):
            a, b = s["start"], s["end"]
            settle = min(b - .3, a + 1.1) if b - a > 1.4 else (a + b) / 2
            page.evaluate(f"window.seek({settle})")
            img = Image.open(io.BytesIO(page.screenshot(type="jpeg", quality=88)))
            img.save(chk / f"scene-{si + 1:02d}.jpg", quality=88)
            thumbs.append((si, settle, img.resize((270, 480))))
            strip = Image.new("RGB", (4 * 270 + 50, 520), "white")
            dr = ImageDraw.Draw(strip)
            for k, t in enumerate([min(a + off, b - .05) for off in (0.05, 0.22, 0.55)] + [b - .12]):
                page.evaluate(f"window.seek({t})")
                fr = Image.open(io.BytesIO(page.screenshot(type="jpeg", quality=80))).resize((270, 480))
                strip.paste(fr, (10 + k * 280, 30))
                dr.text((14 + k * 280, 8), f"{t:.2f}s", fill="black")
            strip.save(chk / f"motion-{si + 1:02d}.jpg", quality=85)

        cols = 5
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 290 + 10, rows * 520 + 10), "white")
        dr = ImageDraw.Draw(sheet)
        for k, (si, t, im) in enumerate(thumbs):
            x, y = 10 + (k % cols) * 290, 10 + (k // cols) * 520
            sheet.paste(im, (x, y + 24))
            dr.text((x, y + 4), f"#{si + 1} {scenes[si]['type']} @ {t:.1f}s", fill="black")
        sheet.save(chk / "contact-sheet.jpg", quality=88)

        # 3. motion: does the picture keep changing?
        prev, still_from, blank = None, None, []
        t = 0.0
        while t < dur:
            page.evaluate(f"window.seek({t})")
            fr = np.asarray(Image.open(io.BytesIO(page.screenshot(type="jpeg", quality=60))).convert("L").resize((108, 192)), dtype=np.float32)
            if fr.std() < 3:
                blank.append(t)
            if prev is not None:
                diff = np.abs(fr - prev).mean()
                if diff < 1.2:
                    still_from = t - args.step if still_from is None else still_from
                else:
                    if still_from is not None and t - still_from > 3.0:
                        issues.append(f"{still_from:.1f}-{t:.1f} s: the picture barely changes for {t - still_from:.1f} s. Add a pop, zoom or new scene.")
                    still_from = None
            prev = fr
            t += args.step
        if still_from is not None and dur - still_from > 3.5:
            issues.append(f"{still_from:.1f} s to the end: the picture barely changes.")
        if blank:
            issues.append(f"Blank-looking frames at {', '.join(f'{x:.1f}s' for x in blank[:6])}.")
        browser.close()

    words = json.loads((folder / "words.json").read_text()) if (folder / "words.json").exists() else []
    if words:
        wps = len(words) / max(0.1, words[-1]["e"] - words[0]["s"])
        notes.append(f"Voice pace: {wps:.1f} words per second (reels feel best around 3).")
    notes.append(f"Length: {dur:.1f} s, {len(scenes)} scenes, a new scene every {dur / max(1, len(scenes)):.1f} s on average.")
    issues = list(dict.fromkeys(issues))
    status = "PASS" if not issues else "FIX"
    rep = [f"# Frame check: {status}", "", *[f"- {n}" for n in notes], ""]
    rep += (["## To fix", "", *[f"- {i}" for i in issues], ""] if issues else ["Nothing to fix. Now look at contact-sheet.jpg and the motion strips yourself."])
    (chk / "report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    say("\n".join(rep))
    say(f"Pictures saved in {chk}")
    sys.exit(0 if not issues else 1)


if __name__ == "__main__":
    main()
