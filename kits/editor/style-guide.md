# My Reel style

Claude reads this before every edit. The `settings` block is used directly by the editing script. The notes below it are for judgement calls. Say "learn my style" with a few Reels you love, and Claude rewrites this for you.

```settings
caption_font: Arial Black
caption_size: 78            # text height in pixels on a 1080x1920 frame
caption_color: #FFFFFF
highlight_color: #FFD43B    # the key word in each caption
outline_color: #000000
outline_width: 6
caption_position: 66        # % from the top; keep under 78 so Instagram's buttons don't cover it
max_words: 3                # words on screen at once
uppercase: true

hook_font: Arial Black
hook_size: 84
hook_color: #111111
hook_box_color: #FFFFFF     # the hook sits on a solid box so it reads on any footage
hook_position: 18           # % from the top
hook_seconds: 2.5

framing: auto               # auto = crop vertical clips, blurred background for horizontal ones
gap: 0.45                   # pauses longer than this many seconds get cut
padding: 0.08               # breathing room kept around each word
cut_fillers: true           # remove um, uh, erm...
music_volume_db: -20        # music level under the voice (it also ducks when you talk)
target_lufs: -14            # loudness for Instagram
whisper_model: base         # base is fast; small is more accurate but slower
```

## Notes

- **Hook:** 3 to 7 words on screen in the first 2 seconds. A bold claim, a number or a question, using my own words from the clip.
- **Pacing:** no pause longer than half a second. If a section is a list, keep each point under 8 seconds.
- **Captions:** big, bold and centred, 1 to 3 words at a time, with one key word highlighted.
- **Graphics:** add a simple animated list or number when I name steps or stats. Otherwise keep the frame clean.
- **Music:** upbeat but quiet, and only from `references/music/`.
- **Length:** aim for 45 to 60 seconds.
