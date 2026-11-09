# Printable invitation

A 5×7" invitation, printed both sides, set up for Vistaprint.

The botanical artwork is not duplicated here — `make_cards.py` reads the
`<symbol>` definitions straight out of `../index.html`, so the cards and the
website are drawing literally the same illustrations. Change the art on the
site, re-run the build, and the cards follow.

## Files to upload

| File | Use |
| --- | --- |
| `invitation-5x7.pdf` | Both sides, page 1 = front, page 2 = back. Start here. |
| `invitation-5x7-front.pdf` | Front only, if the uploader asks per side |
| `invitation-5x7-back.pdf` | Back only |

## Print specification

| | |
| --- | --- |
| Trim size | 5 × 7 in (127 × 178 mm) |
| Document size | 5.25 × 7.25 in — includes 0.125 in bleed on all four edges |
| Safety margin | 0.25 in inside the trim; nothing readable crosses it |
| Colour | CMYK throughout, no RGB |
| Transparency | None — everything is flattened to opaque fills |
| Images | None — 100% vector, so it is sharp at any size |
| Fonts | None — all text is converted to vector outlines (Cormorant Garamond, Jost, Parisienne) |
| Language | Swedish |

On Vistaprint, choose **Invitations & Announcements → 5×7 flat, printed both
sides**, then "Upload your complete design". When it asks whether your file
includes bleed, say yes.

## Rebuilding

```bash
cd print
make
```

`make` only rebuilds when `make_cards.py`, `svgpath.py` or `../index.html` has
changed, and runs `setup.sh` automatically the first time. `make rebuild`
builds even when nothing has changed, `make preview` builds and opens the PDF,
`make setup` reinstalls the toolchain, `make clean` removes the PDFs.

`setup.sh` creates `print/.venv` and downloads the three Google fonts into
`print/.fonts`, pinning the two variable fonts to fixed weights. Neither
directory is committed; the script rebuilds both from scratch.

## Colours

The card is deliberately a little richer than the website: wine-brown text,
maroon accents, sage-green leaves and a warmer gold. The values live in the
`RGB` block near the top of `make_cards.py`, each with the website's original
in a comment, so it is easy to step back towards the site's palette.

Both faces share one ground, set by `CARD_BG`. It is `CREAMS["cream"]`, a
warm golden cream; the `CREAMS` comment lists lighter and less yellow options.

How strongly the leaves print is the `opacity=` on each `art(...)` call in
`front()` and `back()`. The corner sprays sit between 0.6 and 0.9.

## Changing the wording

Everything you would want to reword is in one block near the top of
`make_cards.py` — names, the date in words, the venue, the RSVP deadline, the
QR target, and the three detail sections on the back.

The build prints a warning if any line of text ends up wider than the safe
area, so you will know before it reaches the printer.

## Before you order

- **Publish the website first.** The QR code points at
  `https://axelgard.github.io/wedding/`. It is verified to encode that exact
  URL, but the page has to actually exist by the time the cards go out.
- **The cards are in Swedish, the website is still in English.** Worth making
  those match one way or the other before the invitations go out.
- **Order one proof copy** before the full run, and check the colour. Printed
  terracotta and olive always read a little differently from a screen.
