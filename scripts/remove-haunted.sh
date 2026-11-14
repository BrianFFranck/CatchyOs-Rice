#!/usr/bin/env bash
# Undo install-haunted.sh without touching anything else (the panel is left alone).
# The desktops stay at 5 with their names; change that in System Settings > Virtual Desktops.
set -uo pipefail
DATA=$HOME/.local/share/junji-ito-rice
BK=$DATA/backups

echo ">> wallpaper back to the single Tomie loop (Smart Video Wallpaper)"
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "
var ds = desktops();
for (var i = 0; i < ds.length; i++) {
  var d = ds[i];
  d.wallpaperPlugin = 'luisbocanegra.smart.video.wallpaper.reborn';
  d.reloadConfig();
}" >/dev/null
kpackagetool6 -t Plasma/Wallpaper -r org.junjiito.wallpaper >/dev/null 2>&1

echo ">> Plasma Style"
prev=$(sed -nE "s/^previous plasma theme: '(.*)'$/\1/p" "$BK/plasmarc.theme-before-junji" 2>/dev/null)
plasma-apply-desktoptheme "${prev:-default}" >/dev/null 2>&1 || plasma-apply-desktoptheme default >/dev/null
rm -rf "$HOME/.local/share/plasma/desktoptheme/junji-ito"

echo ">> sounds"
prev=$(sed -nE "s/^previous sound theme: '(.*)'$/\1/p" "$BK/sounds.theme-before-junji" 2>/dev/null)
if [ -n "$prev" ]; then kwriteconfig6 --file kdeglobals --group Sounds --key Theme "$prev"
else kwriteconfig6 --file kdeglobals --group Sounds --key Theme --delete; fi
for g in gtk-3.0 gtk-4.0; do
  [ -f "$HOME/.config/$g/settings.ini" ] && kwriteconfig6 --file "$HOME/.config/$g/settings.ini" --group Settings --key gtk-sound-theme-name --delete
done
kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/startkde" --key Action --delete
kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/exitkde" --key Action --delete
rm -rf "$HOME/.local/share/sounds/junji-ito"

echo ">> KWin effect back to the Burn-My-Windows TV glitch"
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.unloadEffect kwin6_effect_junji_uzumaki >/dev/null 2>&1
kwriteconfig6 --file kwinrc --group Plugins --key kwin6_effect_junji_uzumakiEnabled false
kwriteconfig6 --file kwinrc --group Plugins --key kwin6_effect_tv_glitchEnabled true
rm -rf "$HOME/.local/share/kwin/effects/kwin6_effect_junji_uzumaki"
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.loadEffect kwin6_effect_tv_glitch >/dev/null 2>&1
qdbus6 org.kde.KWin /KWin reconfigure
echo "Haunted desktops removed."
