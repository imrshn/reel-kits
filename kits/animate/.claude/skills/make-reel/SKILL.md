---
name: make-reel
description: Make a finished animated reel from one line ("make a reel about X"). Writes the script, makes the voiceover, animates every scene, times captions to every word, checks every frame, renders the MP4. Use whenever the user asks for a new reel or video.
---

# Make a reel from one line

Goal: `exports/<name>-v1.mp4`, a 20 to 60 second vertical reel that I'd be happy to post. Keep me posted in short lines ("Writing the script...", "Recording the voice...", "Animating 9 scenes...", "Checking every frame...").

If `tools/check.py` hasn't printed READY in this folder before, run it first. Not ready → `setup` skill.

## 1. Start the reel folder

`.venv/bin/python tools/new_reel.py "<the topic>"` (Windows: `.venv\Scripts\python tools\new_reel.py "<the topic>"`). It prints the folder name; use it below as `<name>`.

## 2. Write the script (`reels/<name>/script.md`)

Read `style-guide.md` first. Then write it like a top short-form creator:

- **Length:** 60 to 160 words (about 20 to 55 s). Default ~90 words unless I ask otherwise.
- **First line = the hook.** Name the specific thing in the first 5 words and open a question the viewer needs answered ("Ever noticed airplane food tastes bland?"). Never start with "In this video" or a definition.
- **Then pay it off fast**, one idea per sentence, short sentences (under ~14 words), simple words a 12-year-old knows.
- **Around 60% in, open a fresh question or twist** ("But one taste survives...") so people stay to the end.
- **End within ~5 s of the last payoff** with a short CTA: "Follow for more ..." or, if I gave a comment keyword, "Comment <KEYWORD> and I'll send you ...".
- Spell out what should be said the way it's said ("thirty percent", "twenty twenty-five"), so the voice reads it right.
- Put `*stars*` around 3 to 6 accent words. They show as gold italic in the captions.
- **Facts:** only true, checkable claims. Search to verify if you can. If unsure, cut it. List your sources to me in one line each.

Show me the script and ask "Good to record?" unless I already said to go ahead without asking.

## 3. Record the voice

`.venv/bin/python tools/voice.py <name>`. It uses `settings.json` (free Kokoro voice by default). If I gave you my own recording, use `--file <path>`. Then always:

`.venv/bin/python tools/timing.py <name>`

If timing says many words didn't match, the recording and script.md differ: fix script.md to match what was said, then rerun timing.

## 4. Animate (`reels/<name>/scenes.js`)

Read `REEL-FORMAT.md` and `reels/airplane-food/scenes.js` first. Then plan the scenes from `words.json`:

- **A new scene every 2 to 4 seconds** (one per sentence or half-sentence). Never hold one scene longer than ~5 s; split it or use a `list`/`compare`/`chat` whose items pop in on the spoken words.
- Start each scene with `at:` = the first 2 to 3 words of the sentence it shows, copied exactly from script.md. Item times also use spoken words (`at: "tomato juice"`).
- **On-screen words match the voice** (same idea, fewer words). Headlines 2 to 6 words, one `*accent*` word.
- **Scene 1 = the hook:** `hook` type with an emoji `icon` that matches the subject, the question as `title`.
- **Use the right type:** numbers → `stat`; this vs that → `compare`; reasons/steps → `list` or `steps`; typing/asking → `chat`; real screenshots → `image`; a punchline → `statement`.
- **One contrast moment** at the twist: set `dark: true` on that scene (flips the sky to night). Only one or two per reel.
- End on a `statement` (follow) or `cta` (comment keyword) scene.
- Use `custom` only when no type fits.

## 5. Check every frame (do this before showing me anything)

`.venv/bin/python tools/framecheck.py <name>`

1. Fix everything in `reels/<name>/check/report.md` (text off-screen, overlaps, scenes too long, words not found, picture not changing).
2. **Look at the pictures yourself** with your image reader: `check/contact-sheet.jpg` (one settled frame per scene) and the `check/motion-NN.jpg` strips (4 moments per scene). Ask: Is every word readable? Does each scene show what the voice says at that moment? Is anything cramped, tiny, cut off or covered by the captions? Does it move (things pop in, not just sit there)?
3. Fix `scenes.js` (or `script.md` → re-voice → re-time) and run framecheck again. Repeat until the report says PASS and the pictures look right.

## 6. Render

`.venv/bin/python tools/render.py <name>` (about 3 seconds of work per second of video). It adds a sound on every cut and pop, sets loudness for Instagram (-14 LUFS), and saves `exports/<name>-vN.mp4`.

Then pull 4 frames from the MP4 to confirm it looks like the check pictures (for example with the bundled FFmpeg via `imageio_ffmpeg.get_ffmpeg_exe()`).

## 7. Tell me

3 to 5 short lines: the file path, the length, the hook line, the sources you used, and one idea to make it better. If it's a cloned/AI voice, remind me to switch on Instagram's AI label when posting.
