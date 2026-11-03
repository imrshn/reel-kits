---
name: setup
description: Install and test everything the Reel editor needs (FFmpeg, Whisper, yt-dlp, plus optional HyperFrames and Remotion). Use when the user says "set me up", "install", or when tools/check.py reports something missing.
---

# Set up the Reel editor

Goal: after this, `tools/check.py` prints **READY**. Do it without asking for a password if at all possible. Keep the user updated in short, friendly lines ("Installing the caption tool, this takes a minute or two...").

## 1. Find out what we're working with

Run `python3 --version` (on Windows, try `python --version` and `py --version`). Note the OS.

- **Python 3.9+ found:** go to step 2.
- **Mac, no Python:** run `xcode-select --install`. Tell the user a macOS window will pop up, and they should click **Install** and wait for it (5 to 10 minutes). Then check again.
- **Windows, no Python:** run `winget install -e --id Python.Python.3.12 --scope user`. If winget isn't available, ask them to install Python from python.org and tick "Add python.exe to PATH". Then open a new terminal session and check again.

## 2. Create the private environment and install the core tools

From this folder:

- Mac/Linux: `python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip && .venv/bin/python -m pip install -r tools/requirements.txt`
- Windows: `python -m venv .venv` then `.venv\Scripts\python -m pip install --upgrade pip` then `.venv\Scripts\python -m pip install -r tools\requirements.txt`

This installs Whisper (faster-whisper), yt-dlp and a bundled FFmpeg. Nothing goes outside this folder, and no password is needed. Expect 2 to 5 minutes.

If pip fails, read the error and try the fixes in `TROUBLESHOOTING.md` before asking the user anything.

## 3. FFmpeg

Nothing to do. The kit uses the computer's own FFmpeg if it can draw captions, and otherwise downloads its own copy (about 80 MB) the first time it's needed. No Homebrew or password required.

## 4. Motion graphics add-on (optional, but try it)

HyperFrames and Remotion turn HTML/React into animated overlays. They need Node.js 22 or newer.

- Check `node --version`.
- If Node 22+ exists: in this folder run `npm init -y` (only if there's no package.json) and then `npm install --no-fund --no-audit hyperframes remotion @remotion/cli`.
- If Node is missing or older: tell the user it's optional. Offer the installer from nodejs.org (the LTS version, a normal click-through install), or on Mac `brew install node` if Homebrew exists. Don't block on it. The core editor works without it.

## 5. Test everything

Run `.venv/bin/python tools/check.py` (Windows: `.venv\Scripts\python tools\check.py`).

Then run a real smoke test, so the user knows it works end to end:

1. Make a 6-second test clip with spoken audio. If the system has a text-to-speech command (`say` on Mac, PowerShell's `System.Speech` on Windows), generate a voice line like "Hey, this is a quick test of my new Reel editor. Um, it should cut the pauses and add captions." Combine it with a coloured background using FFmpeg, and save it as `exports/.work/selftest.mp4`.
2. Run `tools/edit.py exports/.work/selftest.mp4 --hook "Setup test" --out exports/.work/selftest-reel.mp4 --no-music`.
3. Confirm the output exists and has a sensible duration.

## 6. Report

Tell the user in plain words what is ready, for example:

> All set. Captions, cutting and exporting work, and I tested it on a sample clip. Motion graphics are ready too.
> Next: drop a clip into raw-footage and say "edit my reel". Optional first: send me 3 to 5 Reels you love and say "learn my style".

If anything optional is missing, mention it in one line with what it adds.
