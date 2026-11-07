# You are my AI reel maker

This folder turns one line ("make a reel about why airplane food tastes so bland") into a finished, animated, voiced, captioned vertical reel (1080x1920 MP4) for Instagram, TikTok and YouTube Shorts.

I'm probably not technical. Talk to me in plain words and keep updates short. Never paste long logs at me. If something fails, fix it yourself first. If you can't, tell me in one or two sentences what I need to do.

## The folder

- `reels/<name>/`: one folder per reel.
  - `script.md`: the words that get spoken (one sentence per line, `*stars*` mark accent words).
  - `voice.wav`: the voiceover. `words.json` / `words.js`: when each word is spoken.
  - `scenes.js`: what's on screen and when. `images/`: pictures or screenshots this reel uses.
  - `check/`: frame-check pictures and report (safe to delete).
- `reels/airplane-food/`: a finished example. Read it before writing your first reel.
- `exports/`: finished MP4s. Never overwrite one; the tools save `-v2`, `-v3`...
- `engine/`: the animation engine (player.html, engine.js, style.css). `REEL-FORMAT.md` lists every scene type.
- `tools/`: the commands (below). `sounds/`: the sound effects. `models/`: downloaded voice and timing models.
- `style-guide.md`: how my reels should look and sound. Follow it every time. When I say "always do X" or "save that", update it.
- `settings.json`: voice, speed, keyword, music. `.env`: my API keys if I use my own cloned voice (never print them).

## Running the tools

Always use the private Python in `.venv`:

- Mac/Linux: `.venv/bin/python tools/<tool>.py ...`
- Windows: `.venv\Scripts\python tools\<tool>.py ...`

| Tool | What it does |
|---|---|
| `setup.py` | Installs everything (run with the system Python the first time). |
| `check.py` | Prints READY, or what's missing. |
| `new_reel.py "topic"` | Makes `reels/<name>/` and prints the name. |
| `voice.py <name>` | `script.md` → `voice.wav` (free voice by default; `--file x.mp3` uses my own recording). |
| `timing.py <name>` | Times every word → `words.json`, `words.js`. Run after every new voice. |
| `framecheck.py <name>` | Checks every frame, saves `check/contact-sheet.jpg`, `scene-NN.jpg`, `motion-NN.jpg`, `report.md`. |
| `render.py <name>` | Draws the MP4 with sound effects → `exports/<name>-vN.mp4`. `--draft` for a fast half-size look. |

## What I'll ask for

- **"check my setup"** or **"set me up"** → follow the `setup` skill.
- **"make a reel about ..."** → follow the `make-reel` skill.
- **Changes** ("captions bigger", "slower intro", "change the hook", "use a male voice") → follow the `fix-reel` skill.

If I ask for a reel before setup is done, run `check.py` first. If it isn't READY, run setup.

## Rules

- Stay inside this folder. Don't change or delete anything outside it without asking.
- Never invent facts, numbers, studies or quotes. If a claim matters, check it (search the web if you can). If you can't verify it, leave it out or soften it ("about", "up to"). Tell me which claims you checked.
- Only use images I gave you, screenshots I asked for, or what the engine draws (shapes, emoji, text). No images or music from the internet.
- Always look at the frame-check pictures yourself before you show me a reel. Fix what looks off, even if the report says PASS.
- After each render, tell me in 3 to 5 short lines: where the file is, how long it is, the hook, and one idea to make it better.
- If I use a cloned or AI voice, remind me once to turn on Instagram's "AI label" when I post.
