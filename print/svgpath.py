"""
A very small SVG subset renderer for ReportLab.

It handles exactly what the wedding site's generated artwork uses: absolute
path commands (M L H V C Q A Z), <circle>, <rect> and <ellipse>, plus the
handful of presentation attributes those shapes carry. That is deliberately
far short of real SVG — it only has to understand our own illustrations.

Fill opacity is resolved by blending against a known flat background rather
than by using PDF transparency, so the output stays fully opaque. Print RIPs
never have to flatten anything.
"""

import math
import re

NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
CMD = re.compile(r"([MmLlHhVvCcQqAaZz])")
TAG = re.compile(r"<(path|circle|rect|ellipse|g|/g)\b([^>]*)>")
ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')


def blend(fg, bg, alpha):
    """Flatten a translucent colour against a known background."""
    return tuple(f * alpha + b * (1 - alpha) for f, b in zip(fg, bg))


# --------------------------------------------------------------- geometry --

def _arc_to_beziers(x0, y0, rx, ry, phi, large_arc, sweep, x1, y1):
    """Endpoint-parameterised SVG arc -> a list of cubic segments."""
    if rx == 0 or ry == 0 or (x0 == x1 and y0 == y1):
        return [("L", x1, y1)]

    rx, ry = abs(rx), abs(ry)
    phi = math.radians(phi % 360)
    cos_p, sin_p = math.cos(phi), math.sin(phi)

    dx2, dy2 = (x0 - x1) / 2.0, (y0 - y1) / 2.0
    x1p = cos_p * dx2 + sin_p * dy2
    y1p = -sin_p * dx2 + cos_p * dy2

    # Scale the radii up if they cannot span the two endpoints
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s

    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(num / den, 0))
    if large_arc == sweep:
        co = -co
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx

    cx = cos_p * cxp - sin_p * cyp + (x0 + x1) / 2.0
    cy = sin_p * cxp + cos_p * cyp + (y0 + y1) / 2.0

    def angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        mod = math.sqrt((ux * ux + uy * uy) * (vx * vx + vy * vy))
        a = math.acos(max(-1.0, min(1.0, dot / mod)))
        return -a if (ux * vy - uy * vx) < 0 else a

    th0 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dth = angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    elif sweep and dth < 0:
        dth += 2 * math.pi

    segs = int(math.ceil(abs(dth) / (math.pi / 2)))
    out = []
    step = dth / segs
    t = (4.0 / 3.0) * math.tan(step / 4.0)

    for i in range(segs):
        a0 = th0 + i * step
        a1 = a0 + step
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)

        def pt(c, s):
            return (cos_p * rx * c - sin_p * ry * s + cx,
                    sin_p * rx * c + cos_p * ry * s + cy)

        p1 = pt(c0, s0)
        p2 = pt(c1, s1)
        d1 = (-rx * s0, ry * c0)
        d2 = (-rx * s1, ry * c1)
        c1x = p1[0] + t * (cos_p * d1[0] - sin_p * d1[1])
        c1y = p1[1] + t * (sin_p * d1[0] + cos_p * d1[1])
        c2x = p2[0] - t * (cos_p * d2[0] - sin_p * d2[1])
        c2y = p2[1] - t * (sin_p * d2[0] + cos_p * d2[1])
        out.append(("C", c1x, c1y, c2x, c2y, p2[0], p2[1]))
    return out


def parse_path(d):
    """Path data -> a flat list of ('M'|'L'|'C'|'Z', *coords) in absolute terms."""
    parts = [p for p in CMD.split(d) if p.strip()]
    ops, i = [], 0
    cur = start = (0.0, 0.0)

    while i < len(parts):
        cmd = parts[i]
        i += 1
        args = []
        if i < len(parts) and not CMD.fullmatch(parts[i]):
            args = [float(n) for n in NUM.findall(parts[i])]
            i += 1

        if cmd in "Zz":
            ops.append(("Z",))
            cur = start
            continue

        k = 0
        first = True
        while k < len(args) or (first and not args):
            if cmd == "M":
                x, y = args[k], args[k + 1]; k += 2
                ops.append(("M", x, y))
                cur = (x, y)
                if first:
                    start = cur
                cmd = "L"          # subsequent pairs after M are implicit L
            elif cmd == "L":
                x, y = args[k], args[k + 1]; k += 2
                ops.append(("L", x, y)); cur = (x, y)
            elif cmd == "H":
                x = args[k]; k += 1
                ops.append(("L", x, cur[1])); cur = (x, cur[1])
            elif cmd == "V":
                y = args[k]; k += 1
                ops.append(("L", cur[0], y)); cur = (cur[0], y)
            elif cmd == "C":
                x1, y1, x2, y2, x, y = args[k:k + 6]; k += 6
                ops.append(("C", x1, y1, x2, y2, x, y)); cur = (x, y)
            elif cmd == "Q":
                qx, qy, x, y = args[k:k + 4]; k += 4
                # quadratic -> cubic
                c1 = (cur[0] + 2.0 / 3 * (qx - cur[0]), cur[1] + 2.0 / 3 * (qy - cur[1]))
                c2 = (x + 2.0 / 3 * (qx - x), y + 2.0 / 3 * (qy - y))
                ops.append(("C", c1[0], c1[1], c2[0], c2[1], x, y)); cur = (x, y)
            elif cmd == "A":
                rx, ry, rot, laf, sf, x, y = args[k:k + 7]; k += 7
                ops.extend(_arc_to_beziers(cur[0], cur[1], rx, ry, rot,
                                           int(laf), int(sf), x, y))
                cur = (x, y)
            else:
                raise ValueError("unsupported path command %r" % cmd)
            first = False
            if not args:
                break
    return ops


# ---------------------------------------------------------------- drawing --

def _emit(c, ops):
    p = c.beginPath()
    for op in ops:
        if op[0] == "M":
            p.moveTo(op[1], op[2])
        elif op[0] == "L":
            p.lineTo(op[1], op[2])
        elif op[0] == "C":
            p.curveTo(*op[1:])
        elif op[0] == "Z":
            p.close()
    return p


def _shape_ops(tag, a):
    """Non-path primitives, expressed as path ops."""
    if tag == "circle":
        cx, cy, r = float(a["cx"]), float(a["cy"]), float(a["r"])
        return _ellipse_ops(cx, cy, r, r)
    if tag == "ellipse":
        return _ellipse_ops(float(a["cx"]), float(a["cy"]),
                            float(a["rx"]), float(a["ry"]))
    if tag == "rect":
        x, y = float(a.get("x", 0)), float(a.get("y", 0))
        w, h = float(a["width"]), float(a["height"])
        r = float(a.get("rx", 0))
        if r <= 0:
            return [("M", x, y), ("L", x + w, y), ("L", x + w, y + h),
                    ("L", x, y + h), ("Z",)]
        d = (f"M{x + r} {y} H{x + w - r} A{r} {r} 0 0 1 {x + w} {y + r} "
             f"V{y + h - r} A{r} {r} 0 0 1 {x + w - r} {y + h} "
             f"H{x + r} A{r} {r} 0 0 1 {x} {y + h - r} "
             f"V{y + r} A{r} {r} 0 0 1 {x + r} {y} Z")
        return parse_path(d)
    return []


def _ellipse_ops(cx, cy, rx, ry):
    k = 0.5522847498
    return [
        ("M", cx + rx, cy),
        ("C", cx + rx, cy + ry * k, cx + rx * k, cy + ry, cx, cy + ry),
        ("C", cx - rx * k, cy + ry, cx - rx, cy + ry * k, cx - rx, cy),
        ("C", cx - rx, cy - ry * k, cx - rx * k, cy - ry, cx, cy - ry),
        ("C", cx + rx * k, cy - ry, cx + rx, cy - ry * k, cx + rx, cy),
        ("Z",),
    ]


def _rotate(ops, deg, ox, oy):
    r = math.radians(deg)
    cos_r, sin_r = math.cos(r), math.sin(r)

    def f(x, y):
        x, y = x - ox, y - oy
        return (x * cos_r - y * sin_r + ox, x * sin_r + y * cos_r + oy)

    out = []
    for op in ops:
        if op[0] == "Z":
            out.append(op)
        else:
            co = []
            for i in range(1, len(op), 2):
                co.extend(f(op[i], op[i + 1]))
            out.append((op[0], *co))
    return out


def draw(c, markup, box, view, color, bg, to_pdf_color,
         opacity=1.0, min_stroke=0.3, stroke_scale=1.0):
    """
    Render one symbol's markup.

    box   - (x, y, w, h) on the page, in points, y measured from the bottom
    view  - (vw, vh) of the symbol's viewBox
    color - the RGB triple that 'currentColor' resolves to
    bg    - the RGB the artwork sits on, used to flatten fill-opacity
    """
    x, y, w, h = box
    vw, vh = view
    s = min(w / vw, h / vh)

    c.saveState()
    # SVG is y-down; move to the top-left of the box and flip
    c.translate(x + (w - vw * s) / 2.0, y + h - (h - vh * s) / 2.0)
    c.scale(s, -s)

    stack = [{"fill": "none", "stroke": "none", "stroke-width": 1.0}]

    for tag, raw in TAG.findall(markup):
        attrs = dict(ATTR.findall(raw))
        if tag == "g":
            st = dict(stack[-1])
            st.update(attrs)
            stack.append(st)
            continue
        if tag == "/g":
            if len(stack) > 1:
                stack.pop()
            continue

        st = dict(stack[-1])
        st.update(attrs)

        ops = parse_path(attrs["d"]) if tag == "path" else _shape_ops(tag, attrs)
        if not ops:
            continue
        if "transform" in st and st["transform"].startswith("rotate"):
            deg, ox, oy = (float(n) for n in NUM.findall(st["transform"])[:3])
            ops = _rotate(ops, deg, ox, oy)

        fill = st.get("fill", "none")
        stroke = st.get("stroke", "none")
        do_fill = fill not in ("none", None)
        do_stroke = stroke not in ("none", None)
        if not (do_fill or do_stroke):
            continue

        if do_fill:
            a = float(st.get("fill-opacity", 1)) * opacity
            c.setFillColor(to_pdf_color(blend(color, bg, a)))
        if do_stroke:
            c.setStrokeColor(to_pdf_color(blend(color, bg, opacity)))
            sw = float(st.get("stroke-width", 1)) * stroke_scale
            c.setLineWidth(max(sw, min_stroke / s))
            c.setLineCap(1)
            c.setLineJoin(1)

        c.drawPath(_emit(c, ops), stroke=int(do_stroke), fill=int(do_fill))

    c.restoreState()
