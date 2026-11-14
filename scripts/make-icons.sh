#!/usr/bin/env bash
# Builds the greyscale "Papirus-Ito" icon theme (~44k icons) in ~/.local/share/icons:
#   Papirus-Ito-Base  = Papirus, greyscale, hidden
#   Papirus-Ito       = Papirus-Dark, greyscale, inherits Papirus-Ito-Base
# Source: the installed papirus-icon-theme package, or a fresh download from GitHub.
# Safe to re-run (it rebuilds both). Takes a minute or two.
set -euo pipefail
cd "$(dirname "$0")/.."
R=$PWD
ICONS=$HOME/.local/share/icons
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

if [ -d /usr/share/icons/Papirus ] && [ -d /usr/share/icons/Papirus-Dark ]; then
  SRC=/usr/share/icons
else
  echo "  downloading Papirus from GitHub"
  curl -fsSL https://github.com/PapirusDevelopmentTeam/papirus-icon-theme/archive/refs/heads/master.tar.gz | tar xz -C "$TMP"
  SRC=$TMP/papirus-icon-theme-master
fi

mkdir -p "$ICONS"
rm -rf "$ICONS/Papirus-Ito-Base" "$ICONS/Papirus-Ito"
cp -a "$SRC/Papirus" "$ICONS/Papirus-Ito-Base"
cp -a "$SRC/Papirus-Dark" "$ICONS/Papirus-Ito"
rm -f "$ICONS"/Papirus-Ito*/icon-theme.cache

# Papirus-Dark links whole folders into ../Papirus: point them at the renamed base
find "$ICONS/Papirus-Ito" -type l | while read -r l; do
  t=$(readlink "$l")
  case "$t" in *Papirus/*) ln -sfn "$(printf '%s' "$t" | sed 's#\(^\|/\)Papirus/#\1Papirus-Ito-Base/#')" "$l" ;; esac
done

sed -i -e 's/^Name=.*/Name=Papirus-Ito-Base/' -e 's/^Comment=.*/Comment=Greyscale Papirus base (used by Papirus-Ito)/' \
       -e 's/^Inherits=.*/Inherits=breeze,hicolor/' "$ICONS/Papirus-Ito-Base/index.theme"
grep -q '^Hidden=' "$ICONS/Papirus-Ito-Base/index.theme" || sed -i 's/^\[Icon Theme\]$/[Icon Theme]\nHidden=true/' "$ICONS/Papirus-Ito-Base/index.theme"
sed -i -e 's/^Name=.*/Name=Papirus-Ito/' -e 's/^Comment=.*/Comment=Greyscale Papirus for the Junji Ito rice/' \
       -e 's/^Inherits=.*/Inherits=Papirus-Ito-Base,breeze-dark,hicolor/' "$ICONS/Papirus-Ito/index.theme"

python3 -I "$R/scripts/greyscale-icons.py" "$ICONS/Papirus-Ito-Base" "$ICONS/Papirus-Ito"
for t in Papirus-Ito-Base Papirus-Ito; do gtk-update-icon-cache -qf "$ICONS/$t" 2>/dev/null || true; done
echo "  Papirus-Ito ready"
