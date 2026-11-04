#!/usr/bin/env python3
"""
Build the printable wedding invitation.

Produces a single 5x7" card, double sided, set up for Vistaprint:
0.125" bleed on every edge and a 0.25" safety margin inside the trim.

The botanical artwork is read straight out of ../index.html, so the cards and
the website are literally drawing the same illustrations. Change the art there
and re-run this to get it on the cards too.

    python3 print/make_cards.py

See print/README.md for the one-time font setup.
"""

import os
import re
import sys

from reportlab import rl_config
from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import segno

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgpath

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(HERE, ".fonts")
OUT = os.path.join(HERE, "invitation-5x7.pdf")
OUT_FRONT = os.path.join(HERE, "invitation-5x7-front.pdf")
OUT_BACK = os.path.join(HERE, "invitation-5x7-back.pdf")


# ===================================================================== copy ==
# Everything you might want to reword lives here.

NAME_A = "Juandré"
NAME_B = "Axel"

WELCOME = "Välkommen till vårt bröllop"

DATE_WORDS = ["Lördagen den 4 september 2027",
              "klockan 15:30"]

VENUE = "KANALMAGASINET"
VENUE_ADDR = "Mem Kanalmagasinet 1 · 614 92 Söderköping"

WEBSITE = "axelgard.github.io/wedding"
QR_URL = "https://axelgard.github.io/wedding/"

# !! CHECK THIS BEFORE ORDERING — pick a real reply-by date.
RSVP_BY = "1 juni 2027"

BACK_LABEL = ""
BACK_TITLE = "PRAKTISK INFORMATION"

DETAILS = [
    ("ico-arch", "Vigseln",
     "Klockan 15:30 på Kanalmagasinet i Mem.\n"
     "Middag och dans följer på samma plats."),
    ("ico-bus", "Bussen",
     "En buss avgår från Norrköpings centralstation klockan 14:35 och\n"
     "kör tillbaka alla när festen är slut. Säg till om ni vill ha plats."),
    ("ico-bed", "Boende",
     "Vi rekommenderar Strand Hotell. Boka direkt på 011-169900\n"
     "eller info@hotellstrand.se och få 20 % rabatt för en natt,\n"
     "eller halva priset på andra natten. Begränsat antal rum."),
    ("ico-dress", "Klädkod",
     "Mörk kostym"),
]

OSA_LABEL = "OSA"
OSA_LINE = "Svara senast " + RSVP_BY
OSA_INFO = "För mer information kan ni besöka vår hemsida"
OSA_NOTE = ["Skanna koden eller skriv in adressen."]


# ================================================================== palette ==
# RGB values taken from the website's :root block, converted to CMYK for
# print. Very light tints drop their black plate so large flat areas of
# cream cannot band.

RGB = {
    "bark":       (0x4a, 0x38, 0x2c),
    "bark_soft":  (0x6b, 0x55, 0x46),
    "olive":      (0x9e, 0x9f, 0x77),
    "olive_deep": (0x6a, 0x6c, 0x4a),
    "rust":       (0xa8, 0x4c, 0x30),
    "gold":       (0xc0, 0xa0, 0x6b),
    "ivory":      (0xfd, 0xf9, 0xf2),
    "linen":      (0xf5, 0xec, 0xe0),
}
RGB = {k: tuple(v / 255.0 for v in c) for k, c in RGB.items()}

# Both faces share one ground so the card reads as a single object.
#
# A cream reads "golden" when the yellow plate runs well above the magenta.
# These step down that ratio rather than just getting lighter, so each one is
# a genuinely different hue. Change the name on the last line.
#
#   linen    0/4/9/0   the original — clearly golden
#   cream    0/3/6/0   golden, but lighter
#   shell    0/2/4/0   warm, noticeably less yellow
#   greige   0/2/2/0   yellow and magenta balanced; warm but neutral
#   paper    0/1/1/0   barely tinted, almost plain stock
CREAMS = {
    "linen":  (0xf5, 0xec, 0xe0),
    "cream":  (0xf7, 0xf1, 0xe9),
    "shell":  (0xf8, 0xf3, 0xee),
    "greige": (0xf8, 0xf4, 0xf2),
    "paper":  (0xfb, 0xf9, 0xf7),
}
CREAMS = {k: tuple(v / 255.0 for v in c) for k, c in CREAMS.items()}

CARD_BG = CREAMS["shell"]


def cmyk(rgb):
    r, g, b = rgb
    k = 1 - max(r, g, b)
    if k >= 1:
        return CMYKColor(0, 0, 0, 1)
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    if k < 0.06:          # keep light tints off the black plate
        k = 0
    return CMYKColor(c, m, y, k)


# ============================================================== page set-up ==

INCH = 72.0
TRIM_W, TRIM_H = 5 * INCH, 7 * INCH
BLEED = 0.125 * INCH
SAFE = 0.25 * INCH

PAGE_W = TRIM_W + 2 * BLEED
PAGE_H = TRIM_H + 2 * BLEED

# Left/bottom of the trim box within the page
TX, TY = BLEED, BLEED
# The safe area everything readable must stay inside
SX, SY = TX + SAFE, TY + SAFE
SW, SH = TRIM_W - 2 * SAFE, TRIM_H - 2 * SAFE
CX = PAGE_W / 2.0


def register_fonts():
    faces = {
        "Cormorant":        "CormorantGaramond-Light.ttf",
        "Cormorant-Reg":    "CormorantGaramond-Regular.ttf",
        "Cormorant-Med":    "CormorantGaramond-Medium.ttf",
        "Jost":             "Jost-Light.ttf",
        "Jost-Reg":         "Jost-Regular.ttf",
        "Script":           "Parisienne-Regular.ttf",
    }
    missing = [f for f in faces.values() if not os.path.exists(os.path.join(FONTS, f))]
    if missing:
        sys.exit("Fonts are not set up yet — run print/setup.sh first.\n"
                 "Missing: " + ", ".join(missing))
    for name, filename in faces.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, filename)))


# ================================================================= artwork ===

def load_symbols():
    """Pull the <symbol> blocks out of the website's inline sprite."""
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'<symbol id="([^"]+)" viewBox="([^"]+)"[^>]*>(.*?)</symbol>',
                         html, re.S):
        name, vb, body = m.groups()
        _, _, vw, vh = (float(n) for n in vb.split())
        # <text> is drawn with real type instead of being traced
        body = re.sub(r"<text.*?</text>", "", body, flags=re.S)
        out[name] = ((vw, vh), body)
    return out


SYM = {}


def art(c, name, box, color, bg, opacity=1.0, stroke_scale=1.0, min_stroke=0.3):
    view, body = SYM[name]
    svgpath.draw(c, body, box, view, color, bg, cmyk,
                 opacity=opacity, min_stroke=min_stroke, stroke_scale=stroke_scale)


# ==================================================================== type ===

OVERSET = []


def text(c, s, y, font, size, color, tracking=0.0, align="c", x=None, leading=None):
    """Draw one line. y is the baseline, measured from the bottom of the page."""
    w = c.stringWidth(s, font, size) + tracking * max(len(s) - 1, 0)
    if align == "c":
        left = CX - w / 2.0
    elif align == "l":
        left = x
    else:
        left = x - w



    # Flag anything that would cross the safe margin. Left-aligned text is
    # checked from where it actually starts, not just on its own width.
    if left + w > SX + SW + 0.001 or left < SX - 0.001:
        OVERSET.append((s, (left + w - SX) / INCH, SW / INCH))

    c.setFillColor(cmyk(color))
    t = c.beginText(left, y)
    t.setFont(font, size)
    # Always set it, including to zero: Tc is part of the PDF text state and
    # persists across BT/ET, so skipping the reset leaks tracking onto every
    # later line.
    t.setCharSpace(tracking)
    t.textOut(s)
    c.drawText(t)
    return w


def block(c, lines, y, font, size, color, leading, tracking=0.0,
          align="c", x=None):
    for line in lines:
        text(c, line, y, font, size, color, tracking, align, x)
        y -= leading
    return y


def rule(c, y, width, color, weight=0.5, x=None):
    c.setStrokeColor(cmyk(color))
    c.setLineWidth(weight)
    x = CX - width / 2.0 if x is None else x
    c.line(x, y, x + width, y)


def background(c, color):
    c.setFillColor(cmyk(color))
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)


# =================================================================== front ===

def front(c):
    bg = CARD_BG
    background(c, bg)

    # Corner greenery, bled off two opposite corners
    art(c, "ill-spray", (TX - 1.05 * INCH, PAGE_H - 2.5 * INCH, 2.9 * INCH, 2.9 * INCH),
        RGB["olive"], bg, opacity=0.42, stroke_scale=0.9)
    c.saveState()
    c.translate(PAGE_W, 0)
    c.scale(-1, 1)
    art(c, "ill-spray", (TX - 1.3 * INCH, -0.25 * INCH, 2.25 * INCH, 2.25 * INCH),
        RGB["olive"], bg, opacity=0.32, stroke_scale=0.9)
    c.restoreState()

    # Wreath with the monogram set inside it
    wreath = 1.62 * INCH
    wy = SY + SH - wreath - 0.34 * INCH
    art(c, "ill-wreath", (CX - wreath / 2, wy, wreath, wreath),
        RGB["olive_deep"], bg, opacity=0.95, stroke_scale=0.85)

    mid = wy + wreath / 2.0
    c.setFont("Cormorant-Reg", 26)
    c.setFillColor(cmyk(RGB["olive_deep"]))
    jw = c.stringWidth("J", "Cormorant-Reg", 26)
    aw = c.stringWidth("A", "Cormorant-Reg", 26)
    c.setFont("Script", 18)
    amp = c.stringWidth("&", "Script", 18)
    gap = 5
    total = jw + gap + amp + gap + aw
    x = CX - total / 2.0
    c.setFont("Cormorant-Reg", 26)
    c.drawString(x, mid - 8.5, "J")
    c.setFont("Script", 18)
    c.setFillColor(cmyk(RGB["rust"]))
    c.drawString(x + jw + gap, mid - 7.5, "&")
    c.setFont("Cormorant-Reg", 26)
    c.setFillColor(cmyk(RGB["olive_deep"]))
    c.drawString(x + jw + gap + amp + gap, mid - 8.5, "A")

    y = wy - 0.3 * INCH
    text(c, WELCOME, y, "Cormorant", 15, RGB["bark_soft"])

    # The names, stacked — far more room than setting them on one line
    y -= 0.8 * INCH
    text(c, NAME_A, y, "Cormorant", 50, RGB["bark"])
    y -= 0.42 * INCH
    text(c, "&", y, "Script", 30, RGB["rust"])
    y -= 0.52 * INCH
    text(c, NAME_B, y, "Cormorant", 50, RGB["bark"])

    y -= 0.4 * INCH
    div = 1.55 * INCH
    art(c, "ill-divider", (CX - div / 2, y - 0.1 * INCH, div, 0.26 * INCH),
        RGB["olive"], bg, opacity=0.85, stroke_scale=1.15)

    y -= 0.54 * INCH
    y = block(c, DATE_WORDS, y, "Cormorant", 15.5, RGB["bark_soft"], 0.27 * INCH)

    y -= 0.2 * INCH
    text(c, VENUE, y, "Jost", 9.2, RGB["bark"], tracking=3.4)
    y -= 0.215 * INCH
    text(c, VENUE_ADDR, y, "Jost", 8, RGB["bark_soft"], tracking=0.25)


# ==================================================================== back ===

def back(c):
    bg = CARD_BG
    background(c, bg)

    # A single sprig, low in the corner, kept well away from the text column
    c.saveState()
    c.translate(PAGE_W, 0)
    c.scale(-1, 1)
    art(c, "ill-sprig", (-0.5 * INCH, -0.42 * INCH, 1.85 * INCH, 2.0 * INCH),
        RGB["olive"], bg, opacity=0.28, stroke_scale=0.9)
    c.restoreState()

    y = SY + SH - 0.2 * INCH
    text(c, BACK_LABEL, y, "Jost", 8, RGB["olive_deep"], tracking=3.2)
    y -= 0.42 * INCH
    text(c, BACK_TITLE, y, "Cormorant", 26, RGB["bark"])

    y -= 0.2 * INCH
    div = 1.3 * INCH
    art(c, "ill-divider", (CX - div / 2, y - 0.16 * INCH, div, 0.22 * INCH),
        RGB["olive"], bg, opacity=0.8, stroke_scale=1.2)

    # --- the detail blocks ---
    y -= 0.42 * INCH
    icon = 0.3 * INCH
    text_x = SX + 0.52 * INCH

    for name, heading, body in DETAILS:
        art(c, name, (SX + 0.02 * INCH, y - 0.055 * INCH, icon, icon),
            RGB["olive_deep"], bg, stroke_scale=0.85, min_stroke=0.4)
        text(c, heading, y + 0.035 * INCH, "Cormorant-Reg", 15,
             RGB["bark"], align="l", x=text_x)
        ly = y - 0.2 * INCH
        for line in body.split("\n"):
            text(c, line, ly, "Jost", 8.3, RGB["bark_soft"], align="l", x=text_x)
            ly -= 0.165 * INCH
        y = ly - 0.32 * INCH

    # --- RSVP, with the QR code ---
    y = SY + 2.0 * INCH
    rule(c, y, SW, RGB["gold"], 0.5, x=SX)
    y -= 0.42 * INCH

    qr_size = 1.12 * INCH
    qr_x = SX + 0.04 * INCH
    qr_y = y - qr_size + 0.16 * INCH
    draw_qr(c, QR_URL, qr_x, qr_y, qr_size, RGB["bark"], bg)

    tx = qr_x + qr_size + 0.3 * INCH
    text(c, OSA_LABEL, y, "Jost", 8, RGB["olive_deep"], tracking=3.2, align="l", x=tx)
    text(c, OSA_LINE, y - 0.27 * INCH, "Cormorant-Reg", 15,
         RGB["bark"], align="l", x=tx)
    text(c, OSA_INFO, y - 0.5 * INCH, "Jost", 8.3,
         RGB["bark_soft"], align="l", x=tx)
    text(c, WEBSITE, y - 0.69 * INCH, "Jost-Reg", 9, RGB["rust"],
         tracking=0.2, align="l", x=tx)
    ny = y - 0.94 * INCH
    for line in OSA_NOTE:
        text(c, line, ny, "Jost", 7.6, RGB["bark_soft"], align="l", x=tx)
        ny -= 0.15 * INCH

    text(c, NAME_A + " & " + NAME_B, SY + 0.12 * INCH, "Script", 17, RGB["rust"])


def draw_qr(c, url, x, y, size, fg, bg):
    """Vector QR — stays sharp at any size and adds no raster weight."""
    qr = segno.make(url, error="m")
    matrix = [list(row) for row in qr.matrix]
    n = len(matrix)
    quiet = 2                     # modules of clear space the spec wants
    mod = size / (n + 2 * quiet)

    c.setFillColor(cmyk(bg))
    c.rect(x, y, size, size, stroke=0, fill=1)
    c.setFillColor(cmyk(fg))
    for r, row in enumerate(matrix):
        for col, on in enumerate(row):
            if on:
                c.rect(x + (col + quiet) * mod,
                       y + size - (r + quiet + 1) * mod,
                       mod * 1.02, mod * 1.02, stroke=0, fill=1)


# ==================================================================== main ===

def main():
    register_fonts()
    # ReportLab seeds every document with Helvetica. Point its default at one
    # of our own faces so the PDF contains nothing but embedded fonts.
    rl_config.canvas_basefontname = "Cormorant"
    SYM.update(load_symbols())

    def new_canvas(path):
        c = canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
        c.setTitle("Juandré & Axel — invitation")
        c.setAuthor("Juandré & Axel")
        c.setSubject("5x7 wedding invitation, 0.125in bleed")
        return c

    # Both sides in one file, which is what Vistaprint's uploader expects...
    c = new_canvas(OUT)
    front(c)
    c.showPage()
    back(c)
    c.showPage()
    c.save()

    # ...and one file per side, for the flows that ask for them separately.
    for path, fn in ((OUT_FRONT, front), (OUT_BACK, back)):
        c = new_canvas(path)
        fn(c)
        c.showPage()
        c.save()

    if OVERSET:
        print("WARNING — these lines run wider than the %.2f in safe area:" % (SW / INCH))
        for line, w, safe in OVERSET:
            print("    %.2f in  %r" % (w, line))
    for path in (OUT, OUT_FRONT, OUT_BACK):
        print("wrote %s" % os.path.relpath(path, ROOT))
    print("  page  %.3f x %.3f in  (trim %g x %g in + %g in bleed, %g in safe margin)"
          % (PAGE_W / INCH, PAGE_H / INCH, TRIM_W / INCH, TRIM_H / INCH,
             BLEED / INCH, SAFE / INCH))


if __name__ == "__main__":
    main()
