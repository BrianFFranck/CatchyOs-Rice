#!/usr/bin/env bash
# Downloads the rice's fonts from Google Fonts' GitHub into ~/.local/share/fonts/junji-ito.
#   Zen Old Mincho (UI) · Shippori Mincho B1 (titles) · Yuji Syuku/Boku (brush): SIL OFL 1.1
#   Special Elite (typewriter): Apache 2.0
set -euo pipefail
DIR=$HOME/.local/share/fonts/junji-ito
BASE=https://github.com/google/fonts/raw/main
mkdir -p "$DIR"
get() { [ -s "$DIR/$(basename "$1")" ] || curl -fsSL -o "$DIR/$(basename "$1")" "$BASE/$1"; echo "  $(basename "$1")"; }
for w in Regular Medium SemiBold Bold Black; do get ofl/zenoldmincho/ZenOldMincho-$w.ttf; done
for w in Regular Medium SemiBold Bold ExtraBold; do get ofl/shipporiminchob1/ShipporiMinchoB1-$w.ttf; done
get ofl/yujisyuku/YujiSyuku-Regular.ttf
get ofl/yujiboku/YujiBoku-Regular.ttf
get apache/specialelite/SpecialElite-Regular.ttf
fc-cache -f "$DIR" >/dev/null
