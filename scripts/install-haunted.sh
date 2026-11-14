#!/usr/bin/env bash
# "Haunted desktops" add-on (Nov 14): safe to re-run, never touches the panel.
#   * 5 virtual desktops, each with its own animated wallpaper (org.junjiito.wallpaper plugin):
#       1 富江 Tomie · 2 渦巻 Uzumaki · 3 地獄星 Remina · 4 墨 Ink · 5 穴 Amigara
#     switching soaks the next one in through an ink bleed; spirals creep in from the edges
#     the longer the machine stays up (reboot clears them)
#   * Plasma Style "Junji Ito" (manga-panel popups, screentone corners, spiral busy indicator)
#   * Sound theme "Junji Ito" (+ login/logout sounds switched on)
#   * KWin effect "Uzumaki": TV-glitch open, spiral-vortex close (replaces Burn-My-Windows TV glitch)
# Build the videos first if assets/desktops is empty: scripts/build-desktops.sh
# Undo: scripts/remove-haunted.sh
set -euo pipefail
cd "$(dirname "$0")/.."
R=$PWD
DATA=$HOME/.local/share/junji-ito-rice
BK=$DATA/backups
D=$DATA/desktops
mkdir -p "$BK" "$D"
stamp() { [ -e "$BK/$1" ] || cp -a "$2" "$BK/$1" 2>/dev/null || true; }   # first backup wins

echo ">> backups"
stamp appletsrc.before-haunted-desktops "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
stamp kwinrc.before-haunted-desktops "$HOME/.config/kwinrc"
[ -e "$BK/plasmarc.theme-before-junji" ] || echo "previous plasma theme: '$(kreadconfig6 --file plasmarc --group Theme --key name)'" > "$BK/plasmarc.theme-before-junji"
[ -e "$BK/sounds.theme-before-junji" ] || echo "previous sound theme: '$(kreadconfig6 --group Sounds --key Theme)'" > "$BK/sounds.theme-before-junji"

echo ">> wallpapers"
cp "$R"/assets/desktops/*.mp4 "$D/"
cp "$R/assets/tomie-loop.mp4" "$D/1-tomie.mp4"
kpackagetool6 -t Plasma/Wallpaper -u "$R/themes/wallpaper/org.junjiito.wallpaper" >/dev/null 2>&1 ||
  kpackagetool6 -t Plasma/Wallpaper -i "$R/themes/wallpaper/org.junjiito.wallpaper" >/dev/null
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "
var ds = desktops();
for (var i = 0; i < ds.length; i++) {
  var d = ds[i];
  d.wallpaperPlugin = 'org.junjiito.wallpaper';
  d.currentConfigGroup = ['Wallpaper', 'org.junjiito.wallpaper', 'General'];
  d.writeConfig('Video1', '$D/1-tomie.mp4');
  d.writeConfig('Video2', '$D/2-uzumaki.mp4');
  d.writeConfig('Video3', '$D/3-remina.mp4');
  d.writeConfig('Video4', '$D/4-ink.mp4');
  d.writeConfig('Video5', '$D/5-amigara.mp4');
  d.reloadConfig();
}" >/dev/null

echo ">> five named desktops"
M=org.kde.KWin.VirtualDesktopManager
ids() { qdbus6 --literal org.kde.KWin /VirtualDesktopManager org.freedesktop.DBus.Properties.Get $M desktops |
        grep -oE '\(uss\) [0-9]+, "[^"]+"' | sed -E 's/.*"([^"]+)"/\1/'; }
mapfile -t ID < <(ids)
while [ "${#ID[@]}" -gt 5 ]; do                       # windows on removed desktops move left
  qdbus6 org.kde.KWin /VirtualDesktopManager $M.removeDesktop "${ID[-1]}"
  mapfile -t ID < <(ids)
done
while [ "${#ID[@]}" -lt 5 ]; do
  qdbus6 org.kde.KWin /VirtualDesktopManager $M.createDesktop "${#ID[@]}" "new"
  mapfile -t ID < <(ids)
done
NAMES=("富江 · Tomie" "渦巻 · Uzumaki" "地獄星 · Remina" "墨 · Ink" "穴 · Amigara")
for i in 0 1 2 3 4; do qdbus6 org.kde.KWin /VirtualDesktopManager $M.setDesktopName "${ID[$i]}" "tmp-$i"; done
for i in 0 1 2 3 4; do qdbus6 org.kde.KWin /VirtualDesktopManager $M.setDesktopName "${ID[$i]}" "${NAMES[$i]}"; done

echo ">> Plasma Style"
python3 "$R/scripts/gen-plasma-style.py" >/dev/null
mkdir -p "$HOME/.local/share/plasma/desktoptheme"
rm -rf "$HOME/.local/share/plasma/desktoptheme/junji-ito"
cp -r "$R/themes/plasma-style/junji-ito" "$HOME/.local/share/plasma/desktoptheme/"
plasma-apply-desktoptheme junji-ito >/dev/null

echo ">> sounds"
mkdir -p "$HOME/.local/share/sounds"
rm -rf "$HOME/.local/share/sounds/junji-ito"
cp -r "$R/themes/sounds/junji-ito" "$HOME/.local/share/sounds/"
kwriteconfig6 --file kdeglobals --group Sounds --key Theme junji-ito
for g in gtk-3.0 gtk-4.0; do
  [ -f "$HOME/.config/$g/settings.ini" ] && kwriteconfig6 --file "$HOME/.config/$g/settings.ini" --group Settings --key gtk-sound-theme-name junji-ito
done
kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/startkde" --key Action Sound
kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/exitkde" --key Action Sound

echo ">> KWin effect"
mkdir -p "$HOME/.local/share/kwin/effects"
rm -rf "$HOME/.local/share/kwin/effects/kwin6_effect_junji_uzumaki"
cp -r "$R/themes/kwin/kwin6_effect_junji_uzumaki" "$HOME/.local/share/kwin/effects/"
kwriteconfig6 --file kwinrc --group Plugins --key kwin6_effect_tv_glitchEnabled false
kwriteconfig6 --file kwinrc --group Plugins --key kwin6_effect_junji_uzumakiEnabled true
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.unloadEffect kwin6_effect_tv_glitch >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.unloadEffect kwin6_effect_junji_uzumaki >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.loadEffect kwin6_effect_junji_uzumaki >/dev/null
qdbus6 org.kde.KWin /KWin reconfigure

echo "Done. The spirals start creeping in about 20 minutes after boot."
