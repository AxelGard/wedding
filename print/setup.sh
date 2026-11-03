#!/usr/bin/env bash
# One-time setup for building the printable cards.
#
#   ./print/setup.sh          # creates print/.venv and fetches the fonts
#   print/.venv/bin/python print/make_cards.py
#
# Nothing here is committed — .venv and .fonts are both gitignored, so this
# rebuilds the whole toolchain from scratch on any machine.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> python environment"
python3 -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet reportlab segno fonttools

echo "==> fonts"
mkdir -p .fonts && cd .fonts
base="https://raw.githubusercontent.com/google/fonts/main"
curl -sfL "$base/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf" -o CormorantGaramond-var.ttf
curl -sfL "$base/ofl/jost/Jost%5Bwght%5D.ttf" -o Jost-var.ttf
curl -sfL "$base/ofl/parisienne/Parisienne-Regular.ttf" -o Parisienne-Regular.ttf
curl -sfL "$base/ofl/cormorantgaramond/OFL.txt" -o OFL-CormorantGaramond.txt
curl -sfL "$base/ofl/jost/OFL.txt" -o OFL-Jost.txt
curl -sfL "$base/ofl/parisienne/OFL.txt" -o OFL-Parisienne.txt

# Cormorant and Jost ship as variable fonts; ReportLab needs fixed instances.
../.venv/bin/python - <<'PY'
from fontTools import ttLib
from fontTools.varLib import instancer


def rename(font, family, style):
    """Each instance needs its own PostScript name, or ReportLab treats them
    as one font and every weight collapses onto whichever loaded first."""
    ps = "%s-%s" % (family.replace(" ", ""), style)
    full = "%s %s" % (family, style)
    for rec in font["name"].names:
        nid = rec.nameID
        if nid == 1:   rec.string = family
        elif nid == 2: rec.string = style
        elif nid == 4: rec.string = full
        elif nid == 6: rec.string = ps
    return font


for src, family, weights in (
        ("CormorantGaramond-var.ttf", "Cormorant Garamond",
         {"Light": 300, "Regular": 400, "Medium": 500}),
        ("Jost-var.ttf", "Jost", {"Light": 300, "Regular": 400})):
    for style, wght in weights.items():
        inst = instancer.instantiateVariableFont(ttLib.TTFont(src), {"wght": wght})
        rename(inst, family, style)
        inst.save(src.replace("-var.ttf", "-%s.ttf" % style))
        print("   ", src.replace("-var.ttf", "-%s.ttf" % style))
PY

rm -f CormorantGaramond-var.ttf Jost-var.ttf
echo "==> done. build with:  print/.venv/bin/python print/make_cards.py"
