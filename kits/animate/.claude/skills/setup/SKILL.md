---
name: setup
description: Check and install everything the reel maker needs (private Python environment, free voice, word timing, renderer, FFmpeg, browser), then test it on the example reel. Use when the user says "check my setup", "set me up", "install", or when tools/check.py is not READY.
---

# Set up the reel maker

Goal: `tools/check.py` prints **READY** and a test render works. Do it without asking for a password if at all possible. Keep the user updated in short, friendly lines ("Downloading the free voice, about a minute...").

## 1. Python 3.10 or newer

Run `python3 --version` (Windows: `python --version`, then `py --version`). Note the OS.

- **Found 3.10+:** go to step 2.
- **Mac, missing or older:** run `xcode-select --install` (a window pops up; tell the user to click **Install** and wait 5 to 10 minutes). If that still gives Python older than 3.10: if `brew` exists, `brew install python@3.12`; otherwise ask the user to install Python from python.org (the macOS installer, normal click-through) and tell you when it's done.
- **Windows, missing:** run `winget install -e --id Python.Python.3.12 --scope user`. If winget isn't there, ask the user to install Python from python.org and tick **"Add python.exe to PATH"**. Then open a new terminal and check again.

## 2. Run the one-command setup

From this folder:

- Mac/Linux: `python3 tools/setup.py`
- Windows: `python tools\setup.py` (or `py tools\setup.py`)

It makes `.venv`, installs the tools, downloads the free voice and the word-timing model (~220 MB, into `models/`), finds or installs a browser for drawing frames, and ends by running `check.py`. Nothing goes outside this folder. Expect 3 to 8 minutes. It's safe to run again.

If a step fails, read the error and try the fixes in `TROUBLESHOOTING.md` before asking the user anything.

## 3. Test it end to end

Render the example reel that ships with the kit:

- Mac/Linux: `.venv/bin/python tools/render.py airplane-food --draft`
- Windows: `.venv\Scripts\python tools\render.py airplane-food --draft`

Confirm `exports/airplane-food-draft-v1.mp4` exists and is about 29 s long. (Optional: also run `tools/voice.py airplane-food` and `tools/timing.py airplane-food` to test the voice; that replaces the example's voice with a fresh one from this computer.)

## 4. Report

Tell the user in plain words, for example:

> All set. The voice, captions, animation and export all work. I tested it by rendering a sample reel (it's in exports).
> Next: tell me "make a reel about ..." with any topic.

Mention once, briefly: they can use their own cloned voice later (Fish Audio or ElevenLabs keys in `.env`, or "use my recording").
