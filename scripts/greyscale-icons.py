#!/usr/bin/env python3
"""Turn an SVG icon theme fully greyscale (in place).

Every #rgb / #rrggbb / rgb(r,g,b) colour in every regular .svg file is replaced by its
luminance grey. Symlinks are left alone (they point at files we already convert).
References such as url(#abc) or href="#abc" are not colours and are skipped.
"""
import os
import re
import sys

HEX = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9A-Za-z_-])')
RGB = re.compile(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)')


def grey(r, g, b):
    l = round(0.299 * r + 0.587 * g + 0.114 * b)
    return max(0, min(255, l))


def hex_sub(m):
    s = m.string
    start = m.start()
    before = s[max(0, start - 6):start]
    if before.endswith(('href="', "href='", 'url(')) or s[start - 1:start] == '(':
        return m.group(0)
    h = m.group(1)
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    v = grey(r, g, b)
    return f'#{v:02x}{v:02x}{v:02x}'


def rgb_sub(m):
    v = grey(*(int(x) for x in m.groups()))
    return f'rgb({v},{v},{v})'


def main(root):
    n = 0
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.endswith('.svg'):
                continue
            p = os.path.join(dirpath, f)
            if os.path.islink(p):
                continue
            try:
                with open(p, encoding='utf-8') as fh:
                    s = fh.read()
            except UnicodeDecodeError:
                continue
            t = RGB.sub(rgb_sub, HEX.sub(hex_sub, s))
            if t != s:
                with open(p, 'w', encoding='utf-8') as fh:
                    fh.write(t)
                n += 1
    print(f'{root}: {n} files converted to greyscale')


if __name__ == '__main__':
    for r in sys.argv[1:]:
        main(r)
