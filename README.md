# Juandré & Axel — wedding site

A single static page for our wedding on **Saturday 4 September 2027, 15:00** at
Kanalmagasinet, Mem, Söderköping. No build step, no dependencies — hand-written
HTML, CSS and a little JavaScript, served straight from GitHub Pages.

## Files

| Path | What's in it |
| --- | --- |
| `index.html` | The whole page, plus an inline SVG sprite holding the botanical illustrations and icons |
| `css/styles.css` | All styling. The colour palette lives in the `:root` block at the top |
| `js/scripts.js` | Countdown, mobile menu, scroll reveals, "add to calendar" |
| `assets/imgs/` | Photographs |
| `.claude/launch.json` | Local preview config (harmless to keep, harmless to delete) |

## Editing the usual things

**The date or time** — one line, `js/scripts.js`:

```js
var WEDDING = new Date(2027, 8, 4, 15, 0, 0);   // month is 0-indexed: 8 = September
```

Then update the date text in `index.html` (the hero, the RSVP section and the
footer) to match.

**The colours** — the `:root` block at the top of `css/styles.css`. Every colour
on the page comes from those variables, so changing one changes it everywhere.
They were sampled from the "Romantic Rustic Fall" palette:

| Variable | Colour | |
| --- | --- | --- |
| `--rust` | `#a84c30` | brick, used for links and accents |
| `--clay` | `#d08a71` | soft terracotta |
| `--sand` | `#debaa0` | warm sand |
| `--olive` | `#9e9f77` | the greenery |
| `--taupe` | `#a0826a` | mocha |
| `--bark` | `#4a382c` | headings |
| `--ivory` / `--linen` | `#fdf9f2` / `#f5ece0` | the two page grounds |

**The RSVP form, venue and bus links** — search `index.html` for `docs.google.com`
and `maps.app.goo.gl`.

**The illustrations** — the line art in `index.html` is generated, not drawn by
hand. If you want to change it, the leaves and roses are ordinary SVG paths and
can be edited in place; each one is a `<symbol>` near the top of the file.

## Still to fill in

- The "Our story" paragraphs are placeholder copy — worth rewriting in your own words
- Accommodation suggestions in the "Staying over" card
- What to say about gifts, in the note below the detail cards
- A nicer photo for the social-media preview (`og:image` in `<head>`), if you want
  one that isn't the engagement picture

## Previewing locally

```bash
python3 -m http.server 4173
```

Then open <http://localhost:4173>.

## Publishing

Push to `master`, then in the repository settings enable **Pages** with the source
set to the `master` branch, `/ (root)` folder. GitHub serves it a minute later.
