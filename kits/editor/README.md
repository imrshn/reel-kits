# Claude Video Editor

Turn Claude into your Reel editor. Drop in a raw clip, say **"edit my reel"**, and get a vertical, captioned, ready-to-post video back.

- Cuts dead air, long pauses and "um"s
- Burned-in captions with a highlighted key word
- A bold hook title in the first 2 seconds
- Reframes to 1080x1920 (crop, or a blurred background for horizontal footage)
- Music under your voice that drops when you talk
- Learns your style from 3 to 5 Reels you love (inspired by them, not a copy)

## Get started

1. **[Download the kit (ZIP)](https://github.com/imrshn/reel-kits/releases/download/editor/editor-kit.zip)** and unzip it. You get a folder called **AI Video Editor**.
2. Open the **Claude desktop app**, go to the **Code** tab, start a **Local** session and pick the unzipped folder.
3. Type **set me up**, then drop a clip in `raw-footage/` and type **edit my reel**.

Full steps are in [START HERE.md](START%20HERE.md). Stuck? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

**You need:** a Mac or Windows laptop, the Claude desktop app and a paid Claude plan (Pro or higher).

## What's inside

| File | What it does |
| --- | --- |
| `CLAUDE.md` | Tells Claude it's your editor, plus the folder rules |
| `.claude/skills/` | Three routines: `setup`, `learn-my-style`, `edit-reel` |
| `style-guide.md` | Your look (captions, hook, pacing). Claude updates it as it learns. |
| `tools/edit.py` | The editing engine (Whisper + FFmpeg) |
| `tools/check.py` | Checks that everything is installed |

Tools used: [FFmpeg](https://ffmpeg.org), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [yt-dlp](https://github.com/yt-dlp/yt-dlp), and optionally [HyperFrames](https://github.com/heygen-com/hyperframes) and [Remotion](https://www.remotion.dev) for motion graphics. Everything installs inside this folder.

Free to use. Shared from the Instagram Reel "Editing Reels with Claude".
