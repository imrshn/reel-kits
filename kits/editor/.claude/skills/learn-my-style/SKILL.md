---
name: learn-my-style
description: Study 3 to 5 reference Reels the user loves and turn what makes them work into style-guide.md, so every future edit follows that style. Use when the user says "learn my style", shares Reel links to copy the feel of, or wants to change their look.
---

# Learn my style

The output is an updated `style-guide.md`: the `settings` block (which `tools/edit.py` reads) plus the plain-English notes below it. The rule that matters most: **inspired by them, not a copy.**

## 1. Get the references

- If the user pasted links, download each into `references/` with yt-dlp:
  `.venv/bin/yt-dlp -o "references/ref-%(autonumber)02d.%(ext)s" -f "mp4/best" "<link>"` (Windows: `.venv\Scripts\yt-dlp`).
- Instagram often blocks downloads without a login. If a download fails, don't fight it. Ask the user to save the Reel to their computer (or screen-record it) and drop the file into `references/`. Files already in `references/` count too.
- 3 to 5 references is ideal. One is fine to start.

## 2. Study them properly

For each reference:

1. Get the duration and resolution with ffprobe.
2. Find the cuts: `ffmpeg -i ref.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null -` and count the scene changes to get the average shot length.
3. Pull frames to look at: one every second for the first 3 seconds, then one every 3 seconds. Use `ffmpeg -i ref.mp4 -vf "fps=1/3,scale=540:-2" exports/.work/style/ref1-%02d.jpg`, and use `select` for the first 3 seconds. **Look at the frames**, since you can read images.
4. Transcribe the first 10 seconds (`tools/edit.py <ref> --transcribe-only`) to see how the hook is worded.

Note for each one:
- **Hook:** what's on screen and said in the first 2 seconds (text size, position, a question or a bold claim).
- **Pacing:** average shot length and whether there's a cut or zoom every 1 to 2 seconds.
- **Captions:** font style (heavy sans, rounded, serif), case, words per line, position as % from the top, colours, highlight colour, outline or box.
- **Colour and look:** bright/dark, warm/cool, contrast.
- **Graphics:** emoji, arrows, screen recordings, B-roll, zoom-ins, progress bars.
- **Music energy:** calm, upbeat, or none.

## 3. Write the style guide

Update the `settings` block in `style-guide.md` with values that capture the shared style:

- Pick a caption font that is installed on this computer and close to the reference look. Safe choices are `Arial Black`, `Helvetica Neue` (Mac), `Impact` and `Verdana`. Check fonts with `fc-list` (Linux), `system_profiler SPFontsDataType` (Mac, slow) or the Fonts folder on Windows.
- Colours as hex (`#FFD43B`). Position as % from the top. Keep captions above 78%, out of the Instagram buttons.
- `max_words`: 1 to 2 for fast, punchy styles and 3 to 4 for calmer ones.
- `gap`: 0.3 for very tight pacing, 0.45 normal, 0.6 relaxed.

Then rewrite the notes section in plain English: what the hook should look like, the pacing rules, and the graphics to add or avoid, so a human editor could follow it.

## 4. Prove it

If there's a clip in `raw-footage/`, offer to re-render the last edit with the new style. Tell the user in 3 or 4 lines what you learned, for example: "Your references use 2-word yellow captions mid-screen, a cut every 1.5 seconds, and a question as the hook. I've saved that as your style."

## Never

- Never reuse footage, graphics, captions text, music or the creator's branding from references in the user's Reels.
- Never copy a hook word for word. Learn its structure only.
