#!/usr/bin/env python3
"""
Builds the kit website from one content file per Reel.

  site/kits/<slug>.json  ->  docs/<slug>/index.html
  all published kits     ->  docs/index.html (home page with keyword search)

Shared look and behaviour live in docs/assets/kit.css and docs/assets/kit.js,
so every page stays consistent. See site/README.md for the content format.

  python scripts/build_site.py            # build published kits
  python scripts/build_site.py --drafts   # also build drafts (for previews; don't commit them)
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" / "kits"
DOCS = ROOT / "docs"
BASE = "https://imrshn.github.io/reel-kits/"
FONTS = "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Geist+Mono:wght@400;500;600&display=swap"

ICON_DOWNLOAD = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11m0 0-5-5m5 5 5-5M5 20h14"/></svg>'
ICON_LAPTOP = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M2 20h20"/></svg>'
ICON_HOME = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/></svg>'
ICON_SEARCH = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
ICON_OUT = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>'


def esc(s: str) -> str:
    return html.escape(str(s or ""), quote=True)


def inline(s: str) -> str:
    """Escape, then allow `code`, **bold** and *italic* (italic renders in the accent colour in headings)."""
    t = esc(s)
    t = re.sub(r"`([^`]+)`", r'<code class="in">\1</code>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    return t


def prompt_html(s: str) -> str:
    """Escape a prompt, then [[placeholder]] -> highlighted fill and ==key line== -> marker highlight."""
    t = esc(s)
    t = re.sub(r"\[\[(.+?)\]\]", r'<span class="fill">[\1]</span>', t)
    t = re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)
    return t


def prompt_plain(s: str) -> str:
    return re.sub(r"==(.+?)==", r"\1", re.sub(r"\[\[(.+?)\]\]", r"[\1]", s))


def head(title: str, desc: str, url: str, og: str, rel: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{esc(og)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#E6EFFF">
<link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{rel}assets/kit.css">
</head>
"""


# ------------------------------------------------------------- sections
def sec_open(s: dict, default_label: str) -> str:
    sid = esc(s["id"])
    intro = f'<p class="sub">{inline(s["intro"])}</p>' if s.get("intro") else ""
    return (f'<section id="{sid}" class="sec" aria-labelledby="{sid}-h">'
            f'<div><span class="label">{esc(s.get("eyebrow", default_label))}</span>'
            f'<h2 id="{sid}-h">{inline(s.get("title", default_label))}</h2>{intro}</div>')


def render_prompts(s: dict, n0: int) -> str:
    out = [sec_open(s, "Prompts")]
    for i, p in enumerate(s["items"], 1):
        pid = f"p{n0 + i}"
        short = len(p["text"]) < 220 and p["text"].count("\n") < 4
        desc = f'<p>{inline(p["note"])}</p>' if p.get("note") else ""
        out.append(f"""<article class="card">
  <div class="ctop"><span class="chip">{esc(p.get("tag", f"{i:02d}"))}</span><button class="btn sm" type="button" data-copy-target="{pid}">Copy prompt</button></div>
  <h3>{inline(p["title"])}</h3>{desc}
<pre class="prompt{' short' if short else ''}" id="{pid}">{prompt_html(p["text"])}</pre>
  {'' if short else '<button class="more" type="button">Show full prompt</button>'}
</article>""")
    out.append("</section>")
    return "\n".join(out)


def render_tools(s: dict) -> str:
    out = [sec_open(s, "Tools"), '<div class="tools">']
    for t in s["items"]:
        price = f'<span class="price">{esc(t["price"])}</span>' if t.get("price") else ""
        icon = esc(t.get("icon") or t["name"][:1])
        acts = f'<a class="btn sm" href="{esc(t["url"])}" target="_blank" rel="noopener">Open {ICON_OUT}</a>' if t.get("url") else ""
        if t.get("prompt"):
            acts += f'<button class="btn sm light" type="button" data-copy="{esc(t["prompt"])}">Copy prompt</button>'
        out.append(f"""<article class="tool">
  <div class="top"><span class="ic" aria-hidden="true">{icon}</span><div><h3>{inline(t["name"])}</h3>{price}</div></div>
  <p>{inline(t["what"])}</p>
  <div class="acts">{acts}</div>
</article>""")
    out.append("</div></section>")
    return "\n".join(out)


def render_steps(s: dict) -> str:
    out = [sec_open(s, "Steps"), '<ol class="steps">']
    for i, st in enumerate(s["items"], 1):
        out.append(f'<li><span class="n">{i}</span><div><b>{inline(st["title"])}</b><span>{inline(st.get("text", ""))}</span></div></li>')
    out.append("</ol>")
    if s.get("extra"):
        x = s["extra"]
        body = esc(x["code"])
        body = re.sub(r"  #\s?(.*)", r'  <span class="c">\1</span>', body)
        out.append(f'<details class="extra"><summary>{esc(x["summary"])}</summary><pre class="tree">{body}</pre></details>')
    out.append("</section>")
    return "\n".join(out)


def render_fixes(s: dict) -> str:
    out = [sec_open(s, "Fix lines"), f'<p class="tip">{esc(s.get("tip", "Tap one to copy it, then paste it to Claude."))}</p>', '<div class="fixes">']
    for f in s["items"]:
        out.append(f'<button class="fix" type="button" data-copy="{esc(f)}">{esc(f)}</button>')
    out.append("</div></section>")
    return "\n".join(out)


def render_about(s: dict) -> str:
    out = [sec_open(s, "About")]
    if s.get("features"):
        out.append('<div class="does">' + "".join(f'<div><b>{inline(f["title"])}</b><span>{inline(f["text"])}</span></div>' for f in s["features"]) + "</div>")
    if s.get("needs"):
        out.append('<ul class="needs">' + "".join(f"<li>{inline(n)}</li>" for n in s["needs"]) + "</ul>")
    out.append("</section>")
    return "\n".join(out)


def render_quick(k: dict) -> str:
    q = k["quick"]
    dl = q.get("download")
    laptop = q.get("laptop_only", False)
    parts = ['<div class="quick"><i class="br tl"></i><i class="br bbr"></i>',
             f'<div class="qhead"><b>{esc(q.get("title", "Quick start"))}</b><span>{esc(q.get("meta", ""))}</span></div>']
    if dl and laptop:
        parts.append(f'<a class="btn full only-desk" href="{esc(dl["url"])}">{ICON_DOWNLOAD}{esc(dl.get("label", "Download the kit"))}</a>')
        parts.append(f'<button class="btn full only-touch" type="button" data-share="{esc(k["name"])}: open this on my laptop">{ICON_LAPTOP}Send this kit to my laptop</button>')
        parts.append(f'<p class="alt only-touch">On a laptop already? <a href="{esc(dl["url"])}">Download the ZIP</a></p>')
    elif dl:
        parts.append(f'<a class="btn full" href="{esc(dl["url"])}">{ICON_DOWNLOAD}{esc(dl.get("label", "Download"))}</a>')
    if q.get("hint"):
        parts.append(f'<p class="hint">{ICON_LAPTOP}<span>{inline(q["hint"])}</span></p>')
    for i, it in enumerate(q.get("items", []), 1):
        label = f"<code>{esc(it['text'])}</code>" if it.get("mono", True) else f"<strong>{inline(it['text'])}</strong>"
        note = f"<small>{inline(it['note'])}</small>" if it.get("note") else ""
        if it.get("url"):
            act = f'<a class="btn sm" href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(it.get("button", "Open"))}</a>'
        else:
            act = f'<button class="btn sm" type="button" data-copy="{esc(prompt_plain(it.get("copy", it["text"])))}">Copy</button>'
        parts.append(f'<div class="row"><span class="n">{i}</span><span class="t">{label}{note}</span>{act}</div>')
    parts.append("</div>")
    return "\n".join(parts)


RENDER = {"prompts": render_prompts, "tools": render_tools, "steps": render_steps, "fixes": render_fixes, "about": render_about}


def build_kit(k: dict) -> str:
    slug = k["slug"]
    url = f"{BASE}{slug}/"
    og = BASE + k.get("og_image", "assets/og-default.png")
    sections = k.get("sections", [])
    laptop = k.get("quick", {}).get("laptop_only", False)
    tabs = [f'<a class="home" href="../" aria-label="All kits">{ICON_HOME}</a>', '<a href="#start" class="on">Quick start</a>']
    tabs += [f'<a href="#{esc(s["id"])}">{esc(s.get("tab", s["type"].title()))}</a>' for s in sections]
    body = []
    pcount = 0
    for s in sections:
        if s["type"] == "prompts":
            body.append(render_prompts(s, pcount))
            pcount += len(s["items"])
        else:
            body.append(RENDER[s["type"]](s))
    first = sections[0] if sections else None
    if laptop:
        dock_main = f'<button class="btn" type="button" data-share="{esc(k["name"])}: open this on my laptop">Send to my laptop</button>'
    else:
        dock_main = f'<button class="btn" type="button" data-share="{esc(k["name"])}">Send to a friend</button>'
    dock_second = f'<a class="btn light" href="#{esc(first["id"])}">{esc(first.get("tab", first["type"].title()))}</a>' if first else ""
    files = (f' · <a href="https://github.com/imrshn/reel-kits/tree/main/kits/{esc(k["files"])}">Files on GitHub</a>' if k.get("files") else "")
    return head(f'{k["name"]} Kit' if k.get("type") == "Starter kit" else k["name"], k["summary"], url, og, "../") + f"""<body data-url="{esc(url)}">
<nav class="tabs" aria-label="Sections">
  {''.join(tabs)}
</nav>
<main class="wrap">
<section id="start" class="sec">
  <div><span class="label">{esc(k.get("type", "Free kit"))} · Comment <span class="kw">{esc(k["keyword"])}</span></span>
  <h1>{inline(k["headline"])}</h1>{f'<p class="sub">{inline(k["lede"])}</p>' if k.get("lede") else ''}</div>
  {render_quick(k)}
</section>
{chr(10).join(body)}
<footer>
  <span>Found this useful? Send it to a friend who'd use it.</span>
  <span><a href="../">More free kits</a>{files}</span>
  <span class="ver">{esc(k.get("version_label", ""))}</span>
</footer>
</main>
<div class="dock"><div class="in">{dock_main}{dock_second}</div></div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="../assets/kit.js"></script>
</body>
</html>
"""


def build_home(kits: list[dict]) -> str:
    items = []
    for k in kits:
        text = " ".join([k["name"], k["summary"], k.get("type", "")])
        items.append(f"""<li data-kw="{esc(k["keyword"])}" data-text="{esc(text)}"><a class="kit" href="{esc(k["slug"])}/">
  <span class="meta"><span class="chip kw">{esc(k["keyword"])}</span><span class="type">{esc(k.get("type", ""))}</span></span>
  <h3>{esc(k["name"])}</h3>
  <p>{inline(k["summary"])}</p>
  <span class="go">Open the kit →</span>
</a></li>""")
    return head("Reel Kits", "Free kits from my Instagram Reels. Type the keyword from the Reel to find yours.", BASE, BASE + "assets/og-default.png", "") + f"""<body class="no-dock" data-url="{BASE}">
<main class="wrap">
  <header>
    <span class="label">Free kits from my Reels</span>
    <h1>Find your <em>kit</em></h1>
    <p class="sub">Type the keyword you commented on the Reel. Every kit is free.</p>
  </header>
  <div class="search">{ICON_SEARCH}<input id="q" type="search" inputmode="text" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="Type the keyword, e.g. EDITOR" aria-label="Keyword from the Reel"></div>
  <ul class="list">
{chr(10).join(items)}
  </ul>
  <p class="empty" id="none" hidden>No kit with that keyword yet. Check the spelling, or look at the newest kits above.</p>
  <footer><span><a href="https://github.com/imrshn/reel-kits">All kit files on GitHub</a></span></footer>
</main>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="assets/kit.js"></script>
</body>
</html>
"""


def main() -> None:
    drafts = "--drafts" in sys.argv
    kits = []
    for f in sorted(SITE.glob("*.json")):
        k = json.loads(f.read_text(encoding="utf-8"))
        if k.get("draft") and not drafts:
            continue
        kits.append(k)
    kits.sort(key=lambda k: k.get("date", ""), reverse=True)
    for k in kits:
        out = DOCS / k["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_kit(k), encoding="utf-8")
        print("built", out.relative_to(ROOT))
    (DOCS / "index.html").write_text(build_home(kits), encoding="utf-8")
    print("built docs/index.html with", len(kits), "kits")


if __name__ == "__main__":
    main()
