#!/usr/bin/env python3
"""Generates the 'Junji Ito' Plasma Style (desktop theme) into themes/plasma-style/junji-ito.

What changes compared with Breeze (everything else falls back to it):
  dialogs/background   popups, notifications, KRunner, OSDs: ink-black panel, sharp manga-panel
                       double rule, halftone screentone fading out of two corners, deeper shadow
  widgets/background   desktop widgets: same panel
  widgets/tooltip      same, smaller
  widgets/busywidget   the busy spinner is an Uzumaki spiral (tapered, hand-inked feel)
Shadow geometry is taken from Breeze's own SVGs (so Plasma's shadow hints stay valid) and
darkened. Colours come from the active colour scheme (ColorScheme-* classes).
"""
import copy
import gzip
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

SRC = '/usr/share/plasma/desktoptheme/default'
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'themes', 'plasma-style', 'junji-ito')
SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
for p, u in (('inkscape', 'http://www.inkscape.org/namespaces/inkscape'),
             ('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'),
             ('xlink', 'http://www.w3.org/1999/xlink'),
             ('dc', 'http://purl.org/dc/elements/1.1/'), ('cc', 'http://creativecommons.org/ns#'),
             ('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')):
    ET.register_namespace(p, u)

COLOR_STYLE = """
            .ColorScheme-Text { color:#dcdcdc; stop-color:#dcdcdc; }
            .ColorScheme-Background { color:#0b0b0b; stop-color:#0b0b0b; }
            .ColorScheme-Highlight { color:#e8e6e1; stop-color:#e8e6e1; }
            .ColorScheme-ButtonFocus { color:#e8e6e1; stop-color:#e8e6e1; }
            .ColorScheme-NegativeText { color:#8e1b1b; stop-color:#8e1b1b; }
        """


def load(rel):
    with gzip.open(os.path.join(SRC, rel + '.svgz')) as f:
        return ET.parse(f)


def save(tree, rel):
    path = os.path.join(OUT, rel + '.svgz')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = ET.tostring(tree.getroot(), encoding='utf-8', xml_declaration=True)
    with gzip.open(path, 'wb') as f:
        f.write(data)


def q(tag):
    return '{%s}%s' % (SVG, tag)


def el(parent, tag, **attrs):
    e = ET.SubElement(parent, q(tag))
    for k, v in attrs.items():
        e.set(k.replace('_', '-') if k not in ('class_',) else 'class', str(v))
    return e


def set_colors(root):
    for st in root.iter(q('style')):
        if st.get('id') == 'current-color-scheme':
            st.text = COLOR_STYLE
            return
    defs = root.find(q('defs')) or el(root, 'defs')
    s = el(defs, 'style', id='current-color-scheme', type='text/css'); s.text = COLOR_STYLE


def darken_shadows(root, k=1.65):
    for stop in root.iter(q('stop')):
        st = stop.get('style', '')
        parts = dict(p.split(':', 1) for p in st.split(';') if ':' in p)
        if 'stop-opacity' in parts and parts.get('stop-color', '#000') in ('#000', '#000000'):
            parts['stop-opacity'] = '%.4f' % min(1.0, float(parts['stop-opacity']) * k)
            stop.set('style', ';'.join(f'{a}:{b}' for a, b in parts.items()))


FRAME_IDS = ('top', 'bottom', 'left', 'right', 'center', 'topleft', 'topright', 'bottomleft', 'bottomright')


def strip(root, ids):
    """Remove elements with these ids (anywhere in the tree)."""
    for parent in list(root.iter()):
        for c in list(parent):
            if c.get('id') in ids:
                parent.remove(c)


def screentone(g, corner, C, inner):
    """Halftone dots fading out of a corner: the manga-panel shading."""
    sp = 2.5
    cs, sn = math.cos(math.pi / 4), math.sin(math.pi / 4)
    for i in range(-12, 13):
        for j in range(-12, 13):
            u, v = i * sp, j * sp
            x, y = u * cs - v * sn, u * sn + v * cs
            if not (inner + 1.2 <= x <= C - 0.8 and inner + 1.2 <= y <= C - 0.8):
                continue
            d = math.hypot(x, y)
            r = 1.05 * (1 - d / (C * 1.1))
            if r < 0.25:
                continue
            if corner == 'bottomright':
                x, y = C - x, C - y
            el(g, 'circle', cx=f'{x:.2f}', cy=f'{y:.2f}', r=f'{r:.2f}', class_='ColorScheme-Text',
               style='fill:currentColor;fill-opacity:0.26')


def add_frame(root, C, margin, bg_opacity, tone=True, inner=3.5, prefix=''):
    """The 9-slice manga panel: sharp corners, a 1 px rule and a fainter inner rule."""
    host = el(root, 'g', id=prefix + 'junji-frame', transform='translate(0,-400)')
    E = 32                                 # edge/centre tile length
    pos = {'topleft': (0, 0), 'top': (C, 0), 'topright': (C + E, 0),
           'left': (0, C), 'center': (C, C), 'right': (C + E, C),
           'bottomleft': (0, C + E), 'bottom': (C, C + E), 'bottomright': (C + E, C + E)}
    size = {'topleft': (C, C), 'top': (E, C), 'topright': (C, C), 'left': (C, E), 'center': (E, E),
            'right': (C, E), 'bottomleft': (C, C), 'bottom': (E, C), 'bottomright': (C, C)}
    o_rule = 'fill:currentColor;fill-opacity:0.46'
    i_rule = "fill:currentColor;fill-opacity:0.15"
    for name in FRAME_IDS:
        x, y = pos[name]; w, h = size[name]
        g = el(host, 'g', id=prefix + name, transform=f'translate({x},{y})')
        el(g, 'rect', x=0, y=0, width=w, height=h, class_='ColorScheme-Background',
           style=f'fill:currentColor;fill-opacity:{bg_opacity}')
        t = name in ('top', 'topleft', 'topright')
        b = name in ('bottom', 'bottomleft', 'bottomright')
        l = name in ('left', 'topleft', 'bottomleft')
        r = name in ('right', 'topright', 'bottomright')
        I = int(inner)
        # outer rule
        if t: el(g, 'rect', x=0, y=0, width=w, height=1, class_='ColorScheme-Text', style=o_rule)
        if b: el(g, 'rect', x=0, y=h - 1, width=w, height=1, class_='ColorScheme-Text', style=o_rule)
        if l: el(g, 'rect', x=0, y=1 if t else 0, width=1, height=h - (1 if t else 0) - (1 if b else 0), class_='ColorScheme-Text', style=o_rule)
        if r: el(g, 'rect', x=w - 1, y=1 if t else 0, width=1, height=h - (1 if t else 0) - (1 if b else 0), class_='ColorScheme-Text', style=o_rule)
        # inner rule, I px further in
        x0 = I if l else 0; x1 = w - I if r else w
        y0 = I if t else 0; y1 = h - I if b else h
        if t: el(g, 'rect', x=x0, y=I, width=x1 - x0, height=1, class_='ColorScheme-Text', style=i_rule)
        if b: el(g, 'rect', x=x0, y=h - I - 1, width=x1 - x0, height=1, class_='ColorScheme-Text', style=i_rule)
        if l: el(g, 'rect', x=I, y=y0 + (1 if t else 0), width=1, height=(y1 - y0) - (1 if t else 0) - (1 if b else 0), class_='ColorScheme-Text', style=i_rule)
        if r: el(g, 'rect', x=w - I - 1, y=y0 + (1 if t else 0), width=1, height=(y1 - y0) - (1 if t else 0) - (1 if b else 0), class_='ColorScheme-Text', style=i_rule)
        if tone and name in ('topleft', 'bottomright'):
            screentone(g, name, C, I)
        # blur mask: the same tile, opaque
        m = el(host, 'rect', id=prefix + 'mask-' + name, x=x, y=y + 200, width=w, height=h, style='fill:#000')
    el(host, 'rect', id=prefix + 'hint-tile-center', x=200, y=0, width=5, height=5, style='fill:#f60')
    for side, (w, h) in (('top', (4, margin)), ('bottom', (4, margin)), ('left', (margin, 4)), ('right', (margin, 4))):
        el(host, 'rect', id=f'{prefix}hint-{side}-margin', x=220, y=0, width=w, height=h, style='fill:#f0f')
    for side, (w, h) in (('top', (4, 1e-8)), ('bottom', (4, 1e-8)), ('left', (1e-8, 4)), ('right', (1e-8, 4))):
        el(host, 'rect', id=f'{prefix}hint-{side}-inset', x=240, y=0, width=w, height=h, style='fill:#0f0')


def panel_svg(rel, C, margin, bg_opacity, tone=True):
    tree = load(rel)
    root = tree.getroot()
    strip(root, set(FRAME_IDS) | {'mask-' + n for n in FRAME_IDS} | {'hint-tile-center'} |
          {f'hint-{s}-{k}' for s in ('top', 'bottom', 'left', 'right') for k in ('margin', 'inset')})
    for t in list(root.iter(q('text'))):
        for parent in root.iter():
            if t in list(parent):
                parent.remove(t)
    # the frame groups lived inside a layer group in Breeze; ours go on the root
    set_colors(root)
    darken_shadows(root)
    add_frame(root, C, margin, bg_opacity, tone)
    return tree


def spiral_polygon(cx, cy, R, turns=3.0, w0=0.16, w1=0.035, steps=220):
    """A tapered Archimedean spiral as a filled outline (thick outside, hair-thin centre)."""
    pts_l, pts_r = [], []
    T = turns * 2 * math.pi
    for i in range(steps + 1):
        u = i / steps
        th = u * T
        r = R * (1 - u) * 0.92 + R * 0.04
        w = R * (w0 + (w1 - w0) * u) * (0.6 + 0.4 * min(1, u * 8))
        x, y = cx + r * math.cos(th), cy + r * math.sin(th)
        # normal ~ radial direction for a slowly winding spiral
        nx, ny = math.cos(th), math.sin(th)
        pts_l.append((x + nx * w / 2, y + ny * w / 2))
        pts_r.append((x - nx * w / 2, y - ny * w / 2))
    pts = pts_l + pts_r[::-1]
    return 'M ' + ' L '.join(f'{x:.3f},{y:.3f}' for x, y in pts) + ' Z'


def busywidget():
    tree = load('widgets/busywidget')
    root = tree.getroot()
    set_colors(root)
    for gid in ('busywidget', '22-22-busywidget', '16-16-busywidget'):
        g = next(e for e in root.iter(q('g')) if e.get('id') == gid)
        rect = next(c for c in g if c.tag == q('rect'))
        x, y = float(rect.get('x')), float(rect.get('y'))
        s = float(rect.get('width'))
        for c in list(g):
            if c is not rect:
                g.remove(c)
        d = spiral_polygon(x + s / 2, y + s / 2, s * 0.46, turns=3.2 if s > 5 else 2.4)
        el(g, 'path', d=d, class_='ColorScheme-Text', style='fill:currentColor;fill-opacity:0.92;stroke:none')
    return tree


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {
        "KPlugin": {
            "Authors": [{"Name": "Junji Ito rice"}],
            "Category": "",
            "Description": "Ink-black manga panels, screentone corners, an Uzumaki busy spiral",
            "Id": "junji-ito",
            "License": "LGPL-2.1+ (shadows derived from Breeze)",
            "Name": "Junji Ito",
            "Version": "1.0",
        },
        "X-Plasma-API-Minimum-Version": "6.0",
    }
    json.dump(meta, open(os.path.join(OUT, 'metadata.json'), 'w'), indent=2)
    with open(os.path.join(OUT, 'plasmarc'), 'w') as f:
        f.write('[AdaptiveTransparency]\nenabled=true\n')
    # The shell always wears the ink palette, whatever colour scheme the apps use.
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, '..', 'themes', 'color-schemes', 'JunjiIto.colors')) as f:
        open(os.path.join(OUT, 'colors'), 'w').write(f.read())
    variants = {'': 0.93, 'translucent/': 0.88, 'opaque/': 1.0, 'solid/': 1.0}
    for v, op in variants.items():
        save(panel_svg('dialogs/background', 26, 8, op), v + 'dialogs/background')
        save(panel_svg('widgets/tooltip', 16, 6, op, tone=True), v + 'widgets/tooltip')
        if v != 'opaque/':
            save(panel_svg('widgets/background', 26, 8, op), v + 'widgets/background')
    save(busywidget(), 'widgets/busywidget')
    print('Plasma Style written to', os.path.abspath(OUT))


main()
