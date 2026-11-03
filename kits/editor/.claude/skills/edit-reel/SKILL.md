---
name: edit-reel
description: Edit a raw clip from raw-footage/ into a finished vertical Reel with cuts, captions, a hook title and music, following style-guide.md. Use when the user says "edit my reel", drops a new clip in, or asks for changes to an edit.
---

# Edit my Reel

`tools/edit.py` does the heavy lifting. Your job is the editor's judgement: pick the hook, check the result, and fix what looks off.

Use the kit's Python: `.venv/bin/python` (Windows: `.venv\Scripts\python`). If `.venv` doesn't exist, run the `setup` skill first.

## 1. Transcribe and choose the hook

1. Run `tools/edit.py --transcribe-only` (or pass the clip path if the user named one).
2. Read `exports/.work/<clip>/transcript.txt`.
3. Write the hook title: **3 to 7 words**, a bold claim, a number or a question, taken from what the user actually says. It should make someone stop scrolling. Examples: "I fired my video editor", "3 prompts. Zero editing skills.", "Stop editing Reels by hand".

## 2. First cut

Run `tools/edit.py --hook "<your hook>"`. It cuts pauses and fillers, reframes to 9:16, adds captions and the hook, mixes music from `references/music/` if there is one, and exports to `exports/<clip>-reel.mp4`.

## 3. Check your own work before showing the user

Pull frames: `ffmpeg -ss 0.5 -i exports/<clip>-reel.mp4 -frames:v 1 exports/.work/check-hook.jpg`, plus 2 or 3 more from the middle. Look at them, and check that:

- The hook is readable and not covering the face or the main subject.
- The captions don't overlap the subject's mouth or important on-screen content. If they do, move them with `--set caption_position=NN`.
- The framing isn't cutting off what matters. For a horizontal screen recording, `--set framing=blur` keeps it whole.

Also check the length. Over 75 seconds? Tell the user, and offer to cut a weaker section by finding it in the transcript.

## 4. Motion graphics (when it adds something)

If HyperFrames is installed (`tools/check.py` shows it) and the user names steps, numbers or tools, offer an animated overlay such as a list card, a big number or a tool name.

1. Scaffold it: `npx --no-install hyperframes init exports/.work/graphics/<name> --non-interactive --resolution portrait`. This also offers HyperFrames' own Claude skills, which teach you its composition format. Accept them.
2. Edit its `index.html`: a transparent or style-guide-coloured card, 2 to 4 seconds, using the style guide's colours.
3. Render it: `cd exports/.work/graphics/<name> && npx --no-install hyperframes render -o card.mp4`.
4. Overlay it on the edit with FFmpeg at the moment the transcript says the user mentions it (`overlay=enable='between(t,START,END)'`), and save as a new version.

Keep graphics short and purposeful. Don't add them just to have them.

## 5. Report

In 3 to 5 short lines: the file name, the final length (and how much was cut), the hook used, and one concrete suggestion ("The middle section about pricing runs 12 seconds. Want me to tighten it?").

## Revisions

Map plain requests to changes and re-render. The transcript is cached, so it's fast:

| They say | Do |
| --- | --- |
| "Make the hook bigger" | `--set hook_size=100` (default 84) |
| "Captions too small/big" | `--set caption_size=90` (default 78) |
| "Move captions up" | `--set caption_position=55` (% from top) |
| "Tighter / it drags" | `--set gap=0.3` |
| "Too choppy" | `--set gap=0.7` or `--no-cut` |
| "Music too loud" | `--set music_volume_db=-26` |
| "No music" | `--no-music` |
| "Different highlight colour" | `--set highlight_color=#4ADE80` |
| "Remove this part" | find it in the transcript, then trim with FFmpeg or re-cut |

Save each new version as `-v2`, `-v3`, and so on, using `--out`. When the user says "always" or "keep this", write the change into `style-guide.md`.
