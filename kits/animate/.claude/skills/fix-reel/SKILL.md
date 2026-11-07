---
name: fix-reel
description: Change a finished reel the way you'd talk to a video editor ("captions bigger", "slower", "new hook", "different voice", "that scene feels empty"). Use for any feedback on an existing reel.
---

# Fix a reel from plain-English feedback

Work on the reel I mean (the latest one in `exports/` unless I say otherwise). Find its folder in `reels/`.

## Decide what has to change

| I say something like | Change | Then run |
|---|---|---|
| "change the hook / the words / it's too long" | `script.md` | voice → timing → framecheck → render |
| "faster / slower voice", "male / female voice" | `settings.json` (`speed`, `kokoro_voice`) or `voice.py --speed/--voice` | voice → timing → framecheck → render |
| "use my recording" | `voice.py <name> --file <path>`, then make `script.md` match what was said | timing → framecheck → render |
| "this scene is empty / boring / wrong", "show X when I say Y", "more motion" | `scenes.js` | framecheck → render |
| "captions bigger / smaller / higher", "different colour" | `REEL({...})` options in `scenes.js` (`captionWords`, `colors`) or `engine/style.css` | framecheck → render |
| "louder sound effects", "add music" | `tools/render.py` levels, or `settings.json` `music` (a file I put in `assets/music/`) | render |

Voices for Kokoro: `am_michael`, `am_puck`, `am_adam` (male US), `af_heart`, `af_bella`, `af_nicole` (female US), `bm_george`, `bm_lewis` (male UK), `bf_emma` (female UK).

## Always

1. Make the change. If it's ambiguous, pick the most likely meaning and say which in one line.
2. Run `framecheck.py` and look at `check/contact-sheet.jpg` and the motion strips. Fix anything new.
3. Render. It saves a new version (`-v2`, `-v3`...), so the old one stays.
4. Tell me in 2 to 3 lines what changed and where the new file is.
5. If I say "always do this" or "save that", add it to `style-guide.md`.
