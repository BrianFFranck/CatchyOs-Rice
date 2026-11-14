#!/usr/bin/env bash
# Rewrite PNGs as plain 8-bit truecolour (RGB, or RGBA when the image has alpha).
# GRUB's and noctalia-greeter's PNG loaders choke on 16-bit / grayscale / palette PNGs,
# which ImageMagick produces by default for black-and-white art.
set -euo pipefail
for f in "$@"; do
  if [ "$(magick identify -format '%A' "$f")" = "False" ] || [ "$(magick identify -format '%A' "$f")" = "Undefined" ]; then
    magick "$f" -colorspace sRGB -depth 8 -type TrueColor "PNG24:$f.tmp"
  else
    magick "$f" -colorspace sRGB -depth 8 -type TrueColorAlpha "PNG32:$f.tmp"
  fi
  mv "$f.tmp" "$f"
done
