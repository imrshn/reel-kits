# AI Reel Maker (AI Video Editor folder)

One line in, finished animated reel out, made by Claude Code on your own computer.

- **Script:** Claude writes a hook-first short-form script and checks its facts.
- **Voice:** free Kokoro voice on your computer, or your own recording, Fish Audio or ElevenLabs voice.
- **Animation:** a Sky Hologram motion-graphics engine (HTML) with 10 scene types: hook, statement, stat counter, list, compare, chat, real screenshots with zoom and highlights, steps, comment CTA, and custom.
- **Captions:** every word timed to the voice by a small speech model on your computer.
- **Self-check:** before you see it, Claude checks every frame (text off-screen, overlaps, scenes that drag, frames that don't move) and looks at the pictures itself.
- **Export:** 1080x1920, 30 fps MP4 with a sound effect on every cut, loudness set for Instagram.

Start with **START HERE.md**. Everything installs inside this folder.

## What's inside

```
CLAUDE.md               how Claude works in this folder
.claude/skills/         setup, make-reel, fix-reel
REEL-FORMAT.md          every scene type and option
style-guide.md          your look and voice (Claude updates it when you say "always...")
engine/                 the animation engine (player.html, engine.js, style.css, fonts)
tools/                  setup, check, new_reel, voice, timing, framecheck, render, make_sounds
sounds/                 6 sound effects (made for this kit)
reels/airplane-food/    a finished example
settings.json           voice, speed, keyword, music
```

## Credits and licences

- Fonts: Plus Jakarta Sans, Instrument Serif, Geist Mono (SIL Open Font License).
- Voice model: Kokoro-82M (Apache-2.0) via kokoro-onnx (MIT). Timing model: NVIDIA Parakeet TDT-CTC 110M (CC-BY-4.0) via sherpa-onnx (Apache-2.0). Both download during setup.
- Rendering: Playwright (Apache-2.0), FFmpeg via imageio-ffmpeg.
- Sound effects and the engine: made for this kit, free to use in your videos.
