# Start here

This folder turns Claude into your Reel editor. You film, and Claude cuts the pauses, adds captions and a hook, mixes music and exports a ready-to-post vertical video.

**You need:** a Mac or Windows laptop, the Claude desktop app, and a paid Claude plan (Pro or higher).
**Time:** about 15 minutes the first time, mostly waiting for installs.

## 1. Put this folder somewhere easy

Unzip the download and move the **AI Video Editor** folder to your Desktop or Documents.

## 2. Open it in Claude

1. Open the **Claude desktop app** and go to the **Code** tab.
2. Start a new session, choose **Local**, and select this folder.

## 3. Say "set me up"

Claude installs and tests everything it needs inside this folder. When it asks for permission to run a command, click **Allow**. It finishes with "All set" after testing itself on a sample clip.

## 4. (Optional) Say "learn my style"

Paste links to 3 to 5 Reels you love, or drop the video files into `references/`. Claude studies their hooks, captions and pacing, and saves your style in `style-guide.md`. It's inspired by them, never a copy.

## 5. Drop in a clip and say "edit my reel"

Put a raw video in `raw-footage/`. Talking-to-camera or a voiceover over a screen recording both work. Claude picks a hook, edits, checks its own work, and saves the Reel to `exports/`.

Want music? Put a track you have the rights to in `references/music/` first.

## 6. Ask for changes in plain words

- "Make the hook bigger"
- "It drags in the middle, tighten it"
- "Captions are covering my face, move them down"
- "Music is too loud"
- "Save this as my style"

Something broken? Tell Claude "this didn't work, fix it", or check `TROUBLESHOOTING.md`.
