"""Start a new reel folder:  reels/<name>/ with an empty script.md and scenes.js.

Usage:  python tools/new_reel.py "why airplane food tastes so bland"
Prints the folder name to use with the other tools.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REELS, say, slugify  # noqa: E402

SCRIPT = """# {topic}
# One sentence per line. Lines starting with # are notes and are not spoken.
# Put *stars* around a word to make it an accent word in the captions.

"""

SCENES = """// Scenes for: {topic}
// Each scene starts when the voice says its "at" words. See REEL-FORMAT.md for every scene type.
REEL({{
  hud: "{hud}",
  scenes: [
    {{ at: 0, type: "hook", icon: "✨", kicker: "", title: "" }},
  ]
}});
"""


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('Usage: python tools/new_reel.py "what the reel is about"')
    topic = " ".join(sys.argv[1:]).strip()
    slug = slugify(topic)
    d = REELS / slug
    n = 2
    while d.exists():
        d = REELS / f"{slug}-{n}"
        n += 1
    (d / "images").mkdir(parents=True)
    (d / "script.md").write_text(SCRIPT.format(topic=topic), encoding="utf-8")
    hud = " ".join(topic.upper().split()[:4])[:28].replace('"', "")
    (d / "scenes.js").write_text(SCENES.format(topic=topic.replace('"', "'"), hud=hud), encoding="utf-8")
    say(d.name)


if __name__ == "__main__":
    main()
