# Troubleshooting

Tell Claude "this didn't work, fix it" first. It reads this file too. These are the problems we hit in testing and the fixes.

## Setup

**"python3: command not found" (Mac)**
macOS needs its developer tools. Run `xcode-select --install`, click Install in the pop-up, wait until it finishes, then say "set me up" again.

**"python is not recognized" (Windows)**
Install Python 3.12 from python.org and tick **Add python.exe to PATH** on the first screen. Then close and reopen the Claude session.

**pip error: "externally-managed-environment"**
Something is trying to install outside the kit. Ask Claude to use the kit's own environment: `.venv/bin/python -m pip install -r tools/requirements.txt`.

**pip error mentioning "ctranslate2" or "av", or "no matching distribution"**
Your Python is too new or too old for the caption tool. Ask Claude to "make the .venv with Python 3.12". On a Mac with Homebrew that's `brew install python@3.12`. On Windows, `winget install Python.Python.3.12`.

**The first edit sits at "Transcribing..." for a while**
It's downloading the speech model (about 150 MB), one time only. On slow Wi-Fi this can take a few minutes.

**"FFmpeg was not found" or a download error for FFmpeg**
The kit downloads its own FFmpeg on first use. If your network blocks that, install FFmpeg yourself: on Mac, `brew install ffmpeg`; on Windows, `winget install Gyan.FFmpeg`. Then reopen the session.

## Editing

**"This FFmpeg can't draw captions (built without libass)"**
Your computer has an older FFmpeg that can't draw captions. The kit normally switches to its own copy automatically. If it doesn't, ask Claude to "use the bundled FFmpeg" or update yours (`brew upgrade ffmpeg`).

**Captions are in the wrong font**
That font isn't installed. Ask Claude to "use a font I have installed that looks like this". Arial Black, Impact and Verdana are on almost every computer.

**The cut feels too choppy, or not tight enough**
Say "less choppy" or "tighter". This changes the `gap` setting (0.3 tight, 0.45 normal, 0.7 relaxed).

**My horizontal screen recording got cropped**
Say "don't crop, keep the whole screen". This uses the blurred-background framing.

**Reference download fails ("login required", "rate-limit", "unable to extract")**
Instagram blocks most automatic downloads. Save the Reel to your computer or screen-record it, then drop the file into `references/`.

**It's slow**
A 2-minute clip usually takes 1 to 3 minutes on a recent laptop. Keep raw clips under 10 minutes. `whisper_model: base` in `style-guide.md` is the fast setting.
