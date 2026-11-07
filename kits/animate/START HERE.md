# Start here

This folder turns Claude into your AI reel maker. You type one line, like *"make a reel about why airplane food tastes so bland"*, and Claude writes the script, records the voiceover, animates every scene, times the captions to every word, checks its own frames, and exports a ready-to-post vertical video.

**You need:** a Mac or Windows computer, the **Claude desktop app**, and a paid Claude plan (Pro or higher) for Claude Code.
**Time:** about 10 minutes the first time, mostly waiting for downloads (about 400 MB).

## 1. Put this folder somewhere easy

Unzip the download and move the **AI Video Editor** folder to your Desktop or Documents.

## 2. Open it in Claude

1. Open the **Claude desktop app** and go to the **Code** tab.
2. Start a new session, choose **Local**, and select the **AI Video Editor** folder.

Now Claude can read and write the files in this folder (and only this folder).

## 3. Say "check my setup"

Claude installs what's missing (inside this folder, no password needed) and tests itself by rendering a sample reel. When it asks for permission to run a command, click **Allow**. It finishes with "All set".

## 4. Say what the reel is about, in one line

> Make a reel about why airplane food tastes so bland

Claude writes the script and shows it to you. Say "go". A few minutes later your reel is in the **exports** folder.

## 5. Ask for changes like you would a video editor

- "Make the hook punchier"
- "Use a female voice" / "Speak a bit faster"
- "The third scene feels empty, add the numbers"
- "Captions bigger"
- "Add a comment keyword at the end: GUIDE"

Every change saves a new version (v2, v3...), so you never lose one.

## Your own voice (optional)

The kit comes with a free, natural voice that runs on your computer. To use your own:

- **Your recording:** record the script on your phone, put the file in the folder, and say "use my recording".
- **Your cloned voice:** copy `.env.example` to `.env`, paste your Fish Audio or ElevenLabs key and voice id, and say "use my Fish voice" (or ElevenLabs).

If you post with a cloned or AI voice, switch on Instagram's **AI label** when you post.

Something broken? Tell Claude "this didn't work, fix it", or see `TROUBLESHOOTING.md`.
