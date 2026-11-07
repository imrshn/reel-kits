# scenes.js format

Every reel's `scenes.js` calls `REEL({...})` once. Scenes play in order. Each starts when the voice says its `at` words and ends when the next scene starts.

```js
REEL({
  hud: "FOOD SCIENCE",          // small label top-left (optional)
  scenes: [
    { at: 0, type: "hook", icon: "✈️", kicker: "Food science", title: "Why airplane food tastes *bland*" },
    { at: "It's not the chef", type: "statement", icon: "👨‍🍳", title: "It's not the *chef*." },
  ]
});
```

## Timing with `at`

- **A string** = the moment the voice says those words. Copy 2 to 3 words from `script.md` exactly (punctuation doesn't matter). Phrases are searched in order, so repeated words are fine as long as scenes are in order.
- **A number** on a scene = seconds from the start of the reel (use `0` for the first scene).
- **A number** on an item inside a scene = seconds after that scene starts.
- If a phrase isn't found, framecheck reports it. Fix the words, don't guess times.

## Text

- `*word*` = accent (serif italic, accent colour). Use one per headline.
- `\n` = line break. Text shrinks automatically to fit its box; framecheck warns if it still can't fit (then shorten it).

## Options on any scene

| Option | Effect |
|---|---|
| `dark: true` | Night sky, white text. Use once or twice for the twist / contrast moment. |
| `flash: true` | Quick white flash as the scene starts. |
| `punch: false` | Turn off the small camera punch-in at the start. |
| `captions: false` | Hide captions during this scene. |
| `hud: "TEXT"` | Change the top-left label from this scene on. |
| `sounds: [{at: "word", kind: "ding"}]` | Extra sound effects (`cut`, `pop`, `tick`, `ding`, `type`, `boom`). |

## Scene types

### hook
Opening scene. Floating emoji in holo rings, kicker, big headline.
`{ type: "hook", icon: "✈️", kicker: "Food science", title: "Why airplane food tastes *bland*", sub: "optional chip", subAt: "words" }`

### statement
One idea, centred. Optional emoji orb, kicker, and a body line that pops in later.
`{ type: "statement", icon: "🔊", kicker: "Small text", title: "Engine noise dulls *sweetness*", body: "optional smaller line", bodyAt: "words", size: 140 }`

### stat
A number that counts up.
`{ type: "stat", kicker: "Lufthansa study", value: 30, prefix: "−", suffix: "%", decimals: 0, from: 0, label: "salty and *sweet* taste", labelAt: "salty" }`

### list
2 to 5 items that pop in as they're said. `layout: "grid"` for icon tiles (2 to 6 items).
`{ type: "list", title: "So...", items: [ { at: "nose", icon: "👃", text: "Your nose dries out" }, ... ] }`

### compare
Two cards, the right one is the "winner" and gets the accent.
`{ type: "compare", title: "On a plane, order...", left: { icon: "🥤", label: "Soda", value: "sweet", at: 0.3 }, right: { icon: "🍅", label: "Tomato juice", value: "*umami*", at: "tomato juice" }, vs: "VS" }`

### chat
Chat bubbles. `from: "you"` types itself out; `from: "ai"` pops in. `who` changes the name.
`{ type: "chat", title: "Claude Code", messages: [ { from: "you", text: "make the captions bigger", at: "just tell it" }, { from: "ai", text: "Done. Captions are 20% bigger.", at: "fixes it" } ] }`

### image
A real screenshot or picture in a browser card, with camera moves and marker highlights. Put the file in `reels/<name>/images/`. `width`/`height` = the image's real pixel size. `focus` points are in image pixels; `zoom: 1` fits the width.
```js
{ type: "image", src: "images/repo.png", width: 1400, height: 900, url: "github.com/you/repo", bar: true,
  title: "optional headline",
  focus: [ { at: 0, x: 700, y: 300, zoom: 1 }, { at: "stars", x: 1150, y: 120, zoom: 2.2 } ],
  marks: [ { at: "stars", x: 1080, y: 100, w: 160, h: 44 } ] }
```

### steps
A checklist of steps; earlier ones are ticked, the `active` one is highlighted (0 = first).
`{ type: "steps", title: "The workflow", steps: ["Desktop app", "A folder", "Local chat", "Setup", "One line"], active: 2 }`

### cta
Comment panel with the keyword typing in and a DM chip.
`{ type: "cta", title: "Want the *kit*?", keyword: "ANIMATE", keywordAt: "comment", dm: "Sent! Check your DMs" }`

### custom
Anything else. `html` is placed in the scene; `update(root, lt, H, T)` runs every frame (`lt` = seconds since the scene started). Helpers in `H`: `pop(el, lt, startSeconds)`, `popWords(el, lt, start)`, `typeText(el, text, lt, start)`, `count(el, from, to, lt, start)`, `eo`/`eio`/`back` easing, `P(t, start, duration)` progress 0..1, `rich("*accent*")`. `T("words", fallback)` gives the scene-local time of spoken words. Keep everything a pure function of `lt` (no timers, no randomness) so every frame renders the same.
```js
{ type: "custom",
  html: '<div class="headline abs" id="big" style="left:60px;right:60px;top:700px;text-align:center;font-size:150px">3x</div>',
  update: (root, lt, H) => { H.pop(root.querySelector('#big'), lt, 0.1); } }
```

## REEL options

| Option | Default | Effect |
|---|---|---|
| `hud` | none | Top-left label |
| `counter` | on | `false` hides the "03 / 10" scene counter |
| `colors` | Sky Hologram | e.g. `{ acc: "#E4572E", sun: "#FFB547" }` (CSS variables in engine/style.css) |
| `captionWords` | 3 | Max words on screen at once |
| `captionChars` | 18 | Max characters per caption group |
| `captions` | on | `false` hides all captions |
| `tail` | 1.2 | Seconds after the last word before the reel ends |
| `voice` | `voice.wav` | Audio file in the reel folder |

## Layout rules (framecheck enforces them)

- Scene content stays between y = 300 and y = 1340 (of 1920). Instagram covers the top ~250 px and the bottom ~380 px.
- Captions sit at y ≈ 1395 and must not drop below 1560.
- No text on top of other text. Nothing outside x = 30..1050.
