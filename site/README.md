# Kit pages: how to add a Reel

Every Reel gets one page at `https://imrshn.github.io/reel-kits/<slug>/`. All pages share the same look and behaviour (`docs/assets/kit.css` and `kit.js`), so a new Reel only needs one JSON file.

## Add a new Reel

1. Copy the closest example in `site/kits/`:
   - `editor.json`: a starter kit with a download (files live in `kits/<name>/`)
   - `example-tools.json`: a tool list
   - `example-style.json`: a prompt pack
2. Rename it to `<slug>.json`, then change `slug`, `keyword`, `date` and the content. Remove `"draft": true`.
3. Run `python3 scripts/build_site.py`. This writes `docs/<slug>/index.html` and refreshes the home page list.
4. Commit and push to `main`. The page is live in about a minute.

Drafts (`"draft": true`) are only built with `--drafts`, for previewing. Don't commit their `docs/` folders.

## Page fields

| Field | What it does |
|---|---|
| `slug` | The page address: `/reel-kits/<slug>/` |
| `keyword` | The comment keyword. It's shown on the page and searchable on the home page, and `/reel-kits/#KEYWORD` redirects to the kit |
| `type` | A label such as "Starter kit", "Tool list" or "Prompt pack" |
| `date` | Sorts the home page, newest first |
| `name`, `headline`, `lede`, `summary` | The title, the big heading, the line under it, and the home page card text |
| `og_image` | Optional link preview image under `docs/` (default `assets/og-default.png`) |
| `files` | Optional folder name in `kits/` for the "Files on GitHub" link |
| `download` | Optional ZIP download (see below) |
| `sections` | The page content, in order, right under the headline. Each one becomes a tab |

### `download` (optional)
- `url`, `label` (default "Download full kit")

### The bottom bar
It's pinned on every device and picks its main button by itself: "Download full kit" if the kit has a `download`, otherwise "Copy all N prompts" if it has prompts. "Share" fills the second slot.

### Section types
Every section has `type`, `id`, `tab`, and optionally `eyebrow`, `title` and `intro`.

- `prompts`: `items` of `{ title, note, tag, text }`. Long prompts collapse with "Show full prompt".
- `tools`: `items` of `{ name, price, what, url, prompt, icon }`
- `steps`: `items` of `{ title, text }`, plus an optional `extra: { summary, code }` fold-out
- `fixes`: `items` is a list of short lines that are copied when tapped, plus an optional `tip`
- `about`: `features` of `{ title, text }` and `needs` (a list of strings)

## Text markup
- `` `code` ``, `**bold**`, `*accent colour*` work in titles and notes.
- In prompt text, `[[fill this in]]` shows as a placeholder and `==highlight==` as a highlight. Neither marker is copied.

## Test before pushing
The UI test (Playwright, 5 screen sizes) checks for horizontal scroll, small tap targets, copy buttons, tabs, the dock and search. Ask Claude to run it on any new page.
