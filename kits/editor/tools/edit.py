#!/usr/bin/env python3
"""
Reel editor: turns a raw talking clip into a vertical, captioned Reel.

What it does, in order:
  1. Transcribes the clip with Whisper (word-level timings, cached).
  2. Cuts dead air, long pauses and filler words (um, uh...).
  3. Reframes to 1080x1920 at 30 fps (crop for vertical clips, blurred
     background for horizontal ones).
  4. Burns in 1-4 word captions with a highlighted key word.
  5. Adds a bold hook title for the first seconds (if --hook is given).
  6. Mixes music from references/music under the voice, ducked when you talk.
  7. Normalises loudness for Instagram and exports an MP4 to exports/.

Settings come from style-guide.md (the ```settings block). Flags override them.

Usage:
  python tools/edit.py                      # newest clip in raw-footage/
  python tools/edit.py raw-footage/take1.mov --hook "Stop editing Reels by hand"
  python tools/edit.py --transcribe-only    # just write the transcript
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mts"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
FILLERS = {"um", "umm", "uh", "uhh", "uhm", "erm", "er", "ah", "hmm", "mm", "mhm"}
STOP = set("""a an the and or but so to of in on at for with from by is are was were be been
it its it's this that these those i you he she we they me my your our their them us
just like really very then than there here what when where which who how do does did
not no yes can will would could should have has had get got go going gonna wanna im i'm
you're we're they're that's there's let's don't can't won't""".split())

DEFAULTS = {
    "caption_font": "Arial Black",
    "caption_size": 78,
    "caption_color": "#FFFFFF",
    "highlight_color": "#FFD43B",
    "outline_color": "#000000",
    "outline_width": 6,
    "caption_position": 66,   # % from the top of the frame
    "max_words": 3,
    "uppercase": True,
    "hook_font": "Arial Black",
    "hook_size": 84,
    "hook_color": "#111111",
    "hook_box_color": "#FFFFFF",
    "hook_position": 18,      # % from the top
    "hook_seconds": 2.5,
    "framing": "auto",        # auto | crop | blur
    "gap": 0.45,              # pauses longer than this (seconds) get cut
    "padding": 0.08,          # seconds kept around each word
    "cut_fillers": True,
    "music_volume_db": -20,
    "target_lufs": -14,
    "whisper_model": "base",
}


# ---------------------------------------------------------------- helpers
def say(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str) -> None:
    print(f"\nERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def _has_captions(ff: str) -> bool:
    try:
        out = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True, timeout=30).stdout
        return " subtitles " in out
    except Exception:
        return False


def find_ffmpeg() -> tuple[str, str]:
    """System FFmpeg if it can draw captions, otherwise the bundled static build."""
    ff, fp = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if ff and fp and _has_captions(ff):
        return ff, fp
    try:
        import static_ffmpeg  # type: ignore
        from static_ffmpeg import run as sf_run  # type: ignore
        sff, sfp = sf_run.get_or_fetch_platform_executables_else_raise()
        if _has_captions(sff):
            return sff, sfp
    except Exception:
        pass
    if ff and fp:
        return ff, fp  # render() explains the missing-captions case
    fail("FFmpeg was not found. Ask Claude: 'set me up' to install it.")
    raise SystemExit


def run(cmd: list[str], quiet: bool = True) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        tail = "\n".join(res.stderr.strip().splitlines()[-15:])
        fail(f"This command failed:\n  {' '.join(cmd[:6])} ...\n{tail}")
    return res


def probe(ffprobe: str, path: Path) -> dict:
    res = run([ffprobe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)])
    data = json.loads(res.stdout)
    v = next((s for s in data["streams"] if s.get("codec_type") == "video"), None)
    a = next((s for s in data["streams"] if s.get("codec_type") == "audio"), None)
    if not v:
        fail(f"{path.name} has no video track.")
    if not a:
        fail(f"{path.name} has no audio track, so there is nothing to caption or cut.")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = abs(int(float(sd["rotation"])))
    if str(v.get("tags", {}).get("rotate", "0")) in ("90", "270"):
        rot = 90
    if rot in (90, 270):
        w, h = h, w
    return {"width": w, "height": h, "duration": float(data["format"]["duration"])}


def parse_style(path: Path) -> dict:
    s = dict(DEFAULTS)
    if not path.exists():
        return s
    text = path.read_text(encoding="utf-8")
    m = re.search(r"```settings\s*\n(.*?)```", text, re.S)
    if not m:
        return s
    for line in m.group(1).splitlines():
        line = re.sub(r"\s+#\s.*$", "", line).strip()  # "# comment" needs a space; colours like #FFD43B don't
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        v = v.strip('"').strip("'")
        if k not in DEFAULTS:
            continue
        d = DEFAULTS[k]
        try:
            if isinstance(d, bool):
                s[k] = v.lower() in ("true", "yes", "1", "on")
            elif isinstance(d, int):
                s[k] = int(float(v))
            elif isinstance(d, float):
                s[k] = float(v)
            else:
                s[k] = v
        except ValueError:
            say(f"  note: ignoring style setting {k}: {v!r} (not a valid value)")
    return s


def ass_color(hex_color: str, alpha: int = 0) -> str:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        h = "FFFFFF"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def ass_time(t: float) -> str:
    t = max(0.0, t)
    hh = int(t // 3600)
    mm = int((t % 3600) // 60)
    ss = t % 60
    return f"{hh}:{mm:02d}:{ss:05.2f}"


def clean_word(w: str) -> str:
    return re.sub(r"[^\w'%$€£₹.-]", "", w.lower()).strip(".'-")


# ------------------------------------------------------------ transcribe
def transcribe(ffmpeg: str, clip: Path, work: Path, model_name: str) -> list[dict]:
    h = hashlib.sha1(f"{clip.stat().st_size}|{model_name}".encode())
    with open(clip, "rb") as fh:
        h.update(fh.read(4 * 1024 * 1024))
    key = h.hexdigest()[:12]
    cache = work / f"transcript-{key}.json"
    if cache.exists():
        say("1/6 Transcript found from an earlier run, reusing it.")
        return json.loads(cache.read_text())

    say(f"1/6 Transcribing with Whisper ({model_name} model). The first run downloads the model, ~150 MB...")
    wav = work / "audio16k.wav"
    run([ffmpeg, "-y", "-i", str(clip), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        fail("Whisper is not installed. Ask Claude: 'set me up'.")
    model = WhisperModel(model_name, device="auto", compute_type="int8")
    segments, info = model.transcribe(
        str(wav),
        word_timestamps=True,
        vad_filter=False,
        initial_prompt="Umm, uh, so, like, you know, I mean, okay.",
        condition_on_previous_text=False,
    )
    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append({"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    say(f"    language: {info.language}, {len(words)} words")
    cache.write_text(json.dumps(words))
    (work / "transcript.txt").write_text(" ".join(w["text"] for w in words) + "\n", encoding="utf-8")
    wav.unlink(missing_ok=True)
    return words


# ------------------------------------------------------------------ cuts
def plan_cuts(words: list[dict], duration: float, s: dict, no_cut: bool) -> tuple[list[tuple[float, float]], list[dict]]:
    if no_cut or not words:
        return [(0.0, duration)], words
    pad, gap = s["padding"], s["gap"]
    kept = [w for w in words if not (s["cut_fillers"] and clean_word(w["text"]) in FILLERS)]
    if not kept:
        return [(0.0, duration)], words
    segs: list[list[float]] = []
    for w in kept:
        a, b = max(0.0, w["start"] - pad), min(duration, w["end"] + pad)
        if segs and a - segs[-1][1] <= gap:
            segs[-1][1] = max(segs[-1][1], b)
        else:
            segs.append([a, b])
    # Merge slivers so the cut never jitters.
    merged: list[list[float]] = []
    for a, b in segs:
        if merged and a <= merged[-1][1] + 0.02:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(round(a, 3), round(b, 3)) for a, b in merged], kept


def remap(words: list[dict], segs: list[tuple[float, float]]) -> list[dict]:
    out, offset, i = [], 0.0, 0
    bounds = []
    for a, b in segs:
        bounds.append((a, b, offset))
        offset += b - a
    for w in words:
        mid = (w["start"] + w["end"]) / 2
        while i < len(bounds) and bounds[i][1] < mid:
            i += 1
        if i >= len(bounds):
            break
        a, b, off = bounds[i]
        if not (a <= mid <= b):
            continue
        out.append({"text": w["text"], "start": off + max(0.0, w["start"] - a), "end": off + min(b - a, w["end"] - a)})
    return out


# -------------------------------------------------------------- captions
def chunk_words(words: list[dict], max_words: int, max_chars: int = 18) -> list[list[dict]]:
    chunks: list[list[dict]] = []
    cur: list[dict] = []
    for w in words:
        if clean_word(w["text"]) in FILLERS:
            continue
        txt_len = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
        gap = w["start"] - cur[-1]["end"] if cur else 0
        if cur and (len(cur) >= max_words or txt_len > max_chars or gap > 0.6):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.!?,:;]$", w["text"]):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def pick_highlight(chunk: list[dict]) -> int:
    best, score = -1, 0
    for i, w in enumerate(chunk):
        c = clean_word(w["text"])
        if not c or c in STOP:
            continue
        sc = len(c) + (6 if re.search(r"\d", c) else 0)
        if sc > score:
            best, score = i, sc
    return best if score >= 4 else -1


def wrap_hook(text: str, max_line: int = 16) -> str:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_line:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return r"\N".join(lines)


def build_ass(words: list[dict], total: float, s: dict, hook: str | None) -> str:
    cap_y = int(1920 * s["caption_position"] / 100)
    hook_y = int(1920 * s["hook_position"] / 100)
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{s['caption_font']},{s['caption_size']},{ass_color(s['caption_color'])},{ass_color(s['caption_color'])},{ass_color(s['outline_color'])},{ass_color('#000000', 0x80)},1,0,0,0,100,100,0,0,1,{s['outline_width']},2,5,60,60,0,1
Style: Hook,{s['hook_font']},{s['hook_size']},{ass_color(s['hook_color'])},{ass_color(s['hook_color'])},{ass_color(s['hook_box_color'])},{ass_color(s['hook_box_color'])},1,0,0,0,100,100,0,0,3,22,0,8,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    hook_end = 0.0
    if hook:
        hook_end = min(float(s["hook_seconds"]), total)
        txt = wrap_hook(hook.upper() if s["uppercase"] else hook)
        lines.append(
            f"Dialogue: 2,{ass_time(0)},{ass_time(hook_end)},Hook,,0,0,0,,"
            f"{{\\pos(540,{hook_y})\\fad(0,200)\\fscx92\\fscy92\\t(0,160,\\fscx100\\fscy100)}}{txt}"
        )
    hi = ass_color(s["highlight_color"])
    base = ass_color(s["caption_color"])
    chunks = chunk_words(words, max(1, int(s["max_words"])))
    for n, ch in enumerate(chunks):
        start = ch[0]["start"]
        nxt = chunks[n + 1][0]["start"] if n + 1 < len(chunks) else total
        end = min(max(ch[-1]["end"] + 0.25, start + 0.35), nxt, total)
        if end <= start:
            continue
        h = pick_highlight(ch)
        parts = []
        for i, w in enumerate(ch):
            t = w["text"].upper() if s["uppercase"] else w["text"]
            t = t.replace("{", "(").replace("}", ")")
            parts.append(f"{{\\c{hi}}}{t}{{\\c{base}}}" if i == h else t)
        text = " ".join(parts)
        lines.append(
            f"Dialogue: 1,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,"
            f"{{\\pos(540,{cap_y})\\fscx85\\fscy85\\t(0,90,\\fscx100\\fscy100)}}{text}"
        )
    return hdr + "\n".join(lines) + "\n"


# ---------------------------------------------------------------- render
def esc_filter_path(p: Path) -> str:
    s = str(p.resolve()).replace("\\", "/")
    return s.replace(":", r"\:").replace("'", r"\'")


def render(ffmpeg: str, clip: Path, info: dict, segs: list[tuple[float, float]], ass: Path,
           music: Path | None, s: dict, out: Path, work: Path) -> None:
    W, H = 1080, 1920
    framing = s["framing"]
    if framing == "auto":
        framing = "crop" if info["width"] / info["height"] <= 0.75 else "blur"

    parts = []
    for i, (a, b) in enumerate(segs):
        parts.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0, b - a - 0.012):.3f}:d=0.012[a{i}];")
    concat_in = "".join(f"[v{i}][a{i}]" for i in range(len(segs)))
    fc = "".join(parts) + f"{concat_in}concat=n={len(segs)}:v=1:a=1[vc][ac];"

    if framing == "crop":
        fc += f"[vc]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30[vf];"
    else:
        fc += (f"[vc]split[bg][fg];"
               f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:4,eq=brightness=-0.06[bgb];"
               f"[fg]scale={W}:-2:force_original_aspect_ratio=decrease[fgs];"
               f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=30[vf];")
    fc += f"[vf]subtitles='{esc_filter_path(ass)}'[vout];"

    lufs = s["target_lufs"]
    fc += f"[ac]highpass=f=70,loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample=48000[voice];"
    inputs = ["-i", str(clip)]
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        total = sum(b - a for a, b in segs)
        vol = s["music_volume_db"]
        fc += (f"[voice]asplit[vmix][vkey];"
               f"[1:a]aresample=48000,volume={vol}dB,afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5[mus];"
               f"[mus][vkey]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[duck];"
               f"[vmix][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]")
    else:
        fc += "[voice]anull[aout]"

    script = work / "filter.txt"
    script.write_text(fc, encoding="utf-8")
    ver = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True).stdout
    m = re.search(r"ffmpeg version n?(\d+)", ver)
    fc_opt = "-/filter_complex" if (m and int(m.group(1)) >= 7) else "-filter_complex_script"
    cmd = [ffmpeg, "-y", *inputs, fc_opt, str(script),
           "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 and "Unrecognized option" in res.stderr:
        i = cmd.index(fc_opt)
        cmd[i] = "-filter_complex_script" if fc_opt == "-/filter_complex" else "-/filter_complex"
        res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        tail = "\n".join(res.stderr.strip().splitlines()[-20:])
        if "No such filter: 'subtitles'" in res.stderr:
            fail("This FFmpeg can't draw captions (it was built without libass). See TROUBLESHOOTING.md: 'captions filter missing'.")
        fail(f"Rendering failed:\n{tail}")


# ------------------------------------------------------------------ main
def newest(folder: Path, exts: set[str]) -> Path | None:
    files = [p for p in folder.glob("*") if p.is_file() and p.suffix.lower() in exts]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def main() -> None:
    ap = argparse.ArgumentParser(description="Edit a raw clip into a Reel.")
    ap.add_argument("clip", nargs="?", help="clip to edit (default: newest file in raw-footage/)")
    ap.add_argument("--hook", help="hook title shown for the first seconds")
    ap.add_argument("--music", help="music file (default: newest file in references/music/, if any)")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--no-cut", action="store_true", help="keep every pause")
    ap.add_argument("--style", default=str(ROOT / "style-guide.md"))
    ap.add_argument("--out", help="output file (default: exports/<clip>-reel.mp4)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override one style setting")
    ap.add_argument("--transcribe-only", action="store_true")
    a = ap.parse_args()

    ffmpeg, ffprobe = find_ffmpeg()
    s = parse_style(Path(a.style))
    for kv in a.set:
        if "=" in kv:
            k, v = kv.split("=", 1)
            if k in DEFAULTS:
                d = DEFAULTS[k]
                s[k] = (v.lower() in ("true", "yes", "1")) if isinstance(d, bool) else type(d)(float(v)) if isinstance(d, (int, float)) else v

    clip = Path(a.clip) if a.clip else newest(ROOT / "raw-footage", VIDEO_EXT)
    if not clip or not clip.exists():
        fail("No clip found. Put a video file in raw-footage/ (MP4 or MOV) and try again.")
    clip = clip.resolve()
    say(f"Editing: {clip.name}")
    info = probe(ffprobe, clip)

    out = Path(a.out) if a.out else ROOT / "exports" / f"{clip.stem}-reel.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    work = ROOT / "exports" / ".work" / clip.stem
    work.mkdir(parents=True, exist_ok=True)

    words = transcribe(ffmpeg, clip, work, s["whisper_model"])
    if a.transcribe_only:
        say(f"Transcript saved: {work / 'transcript.txt'}")
        return
    if not words:
        say("  note: no speech found, so no captions or cuts. Rendering the reframed clip only.")

    say("2/6 Finding dead air and filler words...")
    segs, kept = plan_cuts(words, info["duration"], s, a.no_cut)
    new_len = sum(b - a_ for a_, b in segs)
    say(f"    {info['duration']:.1f}s -> {new_len:.1f}s ({info['duration'] - new_len:.1f}s removed, {len(segs)} pieces kept)")

    say("3/6 Writing captions...")
    mapped = remap(kept, segs)
    ass = work / "captions.ass"
    ass.write_text(build_ass(mapped, new_len, s, a.hook), encoding="utf-8")

    music = None
    if not a.no_music:
        music = Path(a.music) if a.music else newest(ROOT / "references" / "music", AUDIO_EXT)
        if music and not music.exists():
            fail(f"Music file not found: {music}")
    say(f"4/6 Music: {music.name if music else 'none (add a track to references/music to use one)'}")

    say("5/6 Rendering the Reel (1080x1920, 30 fps). This can take a few minutes...")
    render(ffmpeg, clip, info, segs, ass, music, s, out, work)

    summary = {
        "output": str(out), "original_seconds": round(info["duration"], 1), "final_seconds": round(new_len, 1),
        "removed_seconds": round(info["duration"] - new_len, 1), "pieces": len(segs),
        "captions": ass.read_text().count(",Cap,,"),
        "hook": a.hook or "", "music": music.name if music else "",
    }
    (work / "summary.json").write_text(json.dumps(summary, indent=2))
    say("6/6 Done.")
    say(f"\nSaved: {out}")
    say(f"Length: {new_len:.1f}s (cut {info['duration'] - new_len:.1f}s of dead air and fillers)")
    if new_len > 90:
        say("Tip: Reels between 45 and 75 seconds tend to perform best. Ask Claude to trim it down.")
    if not a.hook:
        say("Tip: no hook title yet. Rerun with --hook \"Your hook\" (the transcript is cached, so it's quick).")


if __name__ == "__main__":
    main()
