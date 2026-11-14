#!/usr/bin/env python3
"""Generate the 'JunjiIto' Aurorae window decoration.

Frame: ink-black title bar, 1px manga-panel outline (paper white when active),
soft shadow in the padding area.
Buttons: close = Uzumaki spiral, maximize = open eye, restore = half-open eye,
minimize = closed eye, keep-above = needle, all-desktops = concentric rings.
"""
import math
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "JunjiIto"
os.makedirs(OUT, exist_ok=True)

P = 16      # shadow padding
B = 1       # visible border
T = 30      # title bar height
E = 10      # stretchable edge length in the svg

PAPER = "#d9d7d2"
INK = "#080808"
INK_INACTIVE = "#050505"
LINE_INACTIVE = "#262626"
SEPARATOR = "#1c1c1c"
BLOOD = "#a51d1d"


def shadow_defs(prefix, strength):
    s = strength
    lin = lambda n, x1, y1, x2, y2: (
        f'<linearGradient id="{prefix}-sh-{n}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="#000" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="#000" stop-opacity="{s}"/></linearGradient>')
    # corner gradients: centre sits on the corner of the window, radius = padding
    rad = lambda n, cx, cy: (
        f'<radialGradient id="{prefix}-sh-{n}" cx="{cx}" cy="{cy}" fx="{cx}" fy="{cy}" r="1">'
        f'<stop offset="0" stop-color="#000" stop-opacity="{s}"/>'
        f'<stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>')
    return "".join([lin("top", 0, 0, 0, 1), lin("bottom", 0, 1, 0, 0), lin("left", 0, 0, 1, 0),
                    lin("right", 1, 0, 0, 0), rad("tl", 1, 1), rad("tr", 0, 1), rad("bl", 1, 0),
                    rad("br", 0, 0)])


def frame(prefix, sh, ox, oy, title_fill, line):
    """One 9-slice frame laid out from (ox, oy). Plain rects only (Qt SVG is SVG Tiny)."""
    W = P + B          # side element width  (shadow + border)
    TOP = P + T        # top element height  (shadow + title bar)
    BOT = P + B        # bottom element height
    g = []

    def el(name, x, y, w, h, *rects):
        body = "".join(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{f}"/>'
                       for rx, ry, rw, rh, f in rects)
        g.append(f'<g id="{prefix}-{name}" transform="translate({x},{y})">'
                 f'<rect width="{w}" height="{h}" fill="#000" fill-opacity="0"/>{body}</g>')

    u = lambda n: f"url(#{sh}-sh-{n})"
    x0, x1, x2 = ox, ox + W, ox + W + E
    y0, y1, y2 = oy, oy + TOP, oy + TOP + E
    el("topleft", x0, y0, W, TOP,
       (0, 0, P, P, u("tl")), (P, 0, B, P, u("top")), (0, P, P, T, u("left")), (P, P, B, T, line))
    el("top", x1, y0, E, TOP,
       (0, 0, E, P, u("top")), (0, P, E, T, title_fill), (0, P, E, B, line),
       (0, P + T - 1, E, 1, SEPARATOR))
    el("topright", x2, y0, W, TOP,
       (B, 0, P, P, u("tr")), (0, 0, B, P, u("top")), (0, P, B, T, line), (B, P, P, T, u("right")))
    el("left", x0, y1, W, E, (0, 0, P, E, u("left")), (P, 0, B, E, line))
    el("center", x1, y1, E, E, (0, 0, E, E, INK))
    el("right", x2, y1, W, E, (0, 0, B, E, line), (B, 0, P, E, u("right")))
    el("bottomleft", x0, y2, W, BOT,
       (0, 0, P, B, u("left")), (P, 0, B, B, line), (0, B, P, P, u("bl")), (P, B, B, P, u("bottom")))
    el("bottom", x1, y2, E, BOT, (0, 0, E, B, line), (0, B, E, P, u("bottom")))
    el("bottomright", x2, y2, W, BOT,
       (0, 0, B, B, line), (B, 0, P, B, u("right")), (0, B, B, P, u("bottom")), (B, B, P, P, u("br")))
    return "\n".join(g)


deco = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
<defs>{shadow_defs("a", 0.55)}{shadow_defs("i", 0.30)}</defs>
<rect id="hint-stretch-borders" x="390" y="290" width="1" height="1" fill="none"/>
{frame("decoration", "a", 0, 0, INK, PAPER)}
{frame("decoration-inactive", "i", 100, 0, INK_INACTIVE, LINE_INACTIVE)}
</svg>
"""
open(f"{OUT}/decoration.svg", "w").write(deco)

# ---------------------------------------------------------------- buttons
S = 30  # button cell (== title height)
C = S / 2


def spiral_path(turns=2.6, rmax=6.4, steps=140):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a = t * turns * 2 * math.pi
        r = 0.6 + t * (rmax - 0.6)
        pts.append((C + r * math.cos(a - math.pi / 2), C + r * math.sin(a - math.pi / 2)))
    return "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def stroke(d, color, w=1.4, fill="none"):
    return (f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


EYE = f"M {C-8},{C} Q {C},{C-7.5} {C+8},{C} Q {C},{C+7.5} {C-8},{C} Z"


def glyph(kind, color, accent=None, filled=False):
    accent = accent or color
    if kind == "close":
        out = stroke(spiral_path(), color, 1.35)
        if filled:
            out += f'<circle cx="{C}" cy="{C}" r="1.4" fill="{accent}"/>'
        return out
    if kind == "maximize":     # open eye
        iris = (f'<circle cx="{C}" cy="{C}" r="3.1" fill="{accent if filled else "none"}" '
                f'stroke="{color}" stroke-width="1.2"/>'
                f'<circle cx="{C}" cy="{C}" r="1.1" fill="{"#050505" if filled else color}"/>')
        return stroke(EYE, color, 1.3) + iris
    if kind == "restore":      # half-open eye (heavy lid)
        lid = f"M {C-8},{C-0.5} Q {C},{C-3.2} {C+8},{C-0.5}"
        low = f"M {C-8},{C-0.5} Q {C},{C+7.5} {C+8},{C-0.5}"
        iris = f"M {C-3},{C-1.4} A 3,3 0 0,0 {C+3},{C-1.4} Z"
        return stroke(lid, color, 1.6) + stroke(low, color, 1.2) + \
            f'<path d="{iris}" fill="{accent if filled else color}"/>'
    if kind == "minimize":     # closed eye with lashes
        arc = f"M {C-8},{C-1.5} Q {C},{C+5.5} {C+8},{C-1.5}"
        lashes = "".join(stroke(f"M {x1},{y1} L {x2},{y2}", color, 1.1) for x1, y1, x2, y2 in
                         [(C-5, C+1.2, C-6.4, C+4), (C, C+2.1, C, C+5.2), (C+5, C+1.2, C+6.4, C+4)])
        return stroke(arc, color, 1.4) + lashes
    if kind == "keepabove":    # needle
        return stroke(f"M {C},{C+7} L {C},{C-6}", color, 1.2) + \
            f'<ellipse cx="{C}" cy="{C-4.6}" rx="1.3" ry="2.3" fill="none" stroke="{color}" stroke-width="1"/>' + \
            (f'<circle cx="{C}" cy="{C+7}" r="1.2" fill="{accent}"/>' if filled else "")
    if kind == "alldesktops":  # concentric rings
        return "".join(f'<circle cx="{C}" cy="{C}" r="{r}" fill="none" stroke="{color}" stroke-width="1.1"/>'
                       for r in (2, 4.5, 7)) + \
            (f'<circle cx="{C}" cy="{C}" r="1" fill="{accent}"/>' if filled else "")
    raise ValueError(kind)


def button(kind, hover_accent):
    states = [
        ("active", glyph(kind, "#9e9c97")),
        ("hover", glyph(kind, "#ffffff", hover_accent, True)),
        ("pressed", glyph(kind, hover_accent, hover_accent, True)),
        ("deactivated", glyph(kind, "#2e2e2e")),
        ("inactive", glyph(kind, "#3c3c3c")),
        ("hover-inactive", glyph(kind, "#cfcfcf", hover_accent, True)),
    ]
    body = []
    for i, (name, g) in enumerate(states):
        body.append(f'<g id="{name}-center" transform="translate({i*(S+10)},0)">'
                    f'<rect width="{S}" height="{S}" fill="#000" fill-opacity="0"/>{g}</g>')
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{6*(S+10)}" height="{S}">\n'
            + "\n".join(body) + "\n</svg>\n")


for kind, accent in [("close", BLOOD), ("maximize", "#d9d7d2"), ("restore", "#d9d7d2"),
                     ("minimize", "#d9d7d2"), ("keepabove", BLOOD), ("alldesktops", "#d9d7d2")]:
    open(f"{OUT}/{kind}.svg", "w").write(button(kind, accent))

open(f"{OUT}/JunjiItorc", "w").write(f"""[General]
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=180
ActiveTextColor={PAPER}
InactiveTextColor=#555555
UseTextShadow=false
Shadow=true
DecorationPosition=0

[Layout]
BorderLeft={B}
BorderRight={B}
BorderBottom={B}
BorderTop=0
TitleEdgeTop=0
TitleEdgeBottom=0
TitleEdgeLeft=6
TitleEdgeRight=6
TitleEdgeTopMaximized=0
TitleEdgeBottomMaximized=0
TitleEdgeLeftMaximized=4
TitleEdgeRightMaximized=4
TitleBorderLeft=10
TitleBorderRight=10
TitleHeight={T}
ButtonWidth={S}
ButtonHeight={S}
ButtonSpacing=0
ButtonMarginTop=0
ButtonMarginTopMaximized=0
ExplicitButtonSpacer=8
PaddingTop={P}
PaddingBottom={P}
PaddingLeft={P}
PaddingRight={P}
""")

open(f"{OUT}/metadata.desktop", "w").write("""[Desktop Entry]
Name=Junji Ito
Comment=Ink-black manga panel frames. Close is a spiral, the other buttons are eyes.
X-KDE-PluginInfo-Author=Junji Ito rice
X-KDE-PluginInfo-Name=JunjiIto
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-License=GPL
X-KDE-PluginInfo-Category=
X-Plasma-API=declarativeappletscript
""")
print("aurorae theme written to", OUT)
