#!/usr/bin/env bash
# Junji Ito rice: everything that lives in your home folder (no root needed).
# Safe to re-run. A fresh backup is taken first; scripts/restore.sh undoes it.
set -euo pipefail
cd "$(dirname "$0")/.."
R=$PWD
D=$HOME/.local/share/junji-ito-rice
CFG=$HOME/.config
kw() { kwriteconfig6 "$@"; }
step() { printf '\n\033[97m꩜ %s\033[0m\n' "$*"; }

step "Backing up current configuration"
"$R/scripts/backup.sh"

step "Assets"
[ -f "$R/assets/tomie-loop.mp4" ] || "$R/scripts/build-assets.sh"
mkdir -p "$D"
cp "$R"/assets/{tomie-loop.mp4,tomie-still.png,uzumaki-login.png,term-bg.png,spiral-512.png} "$D/"
cp "$R"/themes/icons/*.svg "$D/"

step "Fonts (Zen Old Mincho, Shippori Mincho B1, Yuji Syuku, Special Elite)"
[ -f "$HOME/.local/share/fonts/junji-ito/ZenOldMincho-Medium.ttf" ] || "$R/scripts/get-fonts.sh"
fc-cache -f "$HOME/.local/share/fonts" >/dev/null

step "Color scheme, window decoration, global theme, widgets"
install -Dm644 "$R/themes/color-schemes/JunjiIto.colors" "$HOME/.local/share/color-schemes/JunjiIto.colors"
mkdir -p "$HOME/.local/share/aurorae/themes"
rm -rf "$HOME/.local/share/aurorae/themes/JunjiIto"
cp -r "$R/themes/aurorae/JunjiIto" "$HOME/.local/share/aurorae/themes/"
kpkg() { # type dir
  kpackagetool6 -t "$1" -u "$2" >/dev/null 2>&1 || kpackagetool6 -t "$1" -i "$2" >/dev/null
}
kpkg Plasma/LookAndFeel "$R/themes/look-and-feel/org.junjiito.desktop"
for p in "$R"/themes/plasmoids/*/; do kpkg Plasma/Applet "$p"; done
# third-party widgets the panel uses (Kara pager, GPL-3, bundled in case the store copy moves)
[ -d "$HOME/.local/share/plasma/plasmoids/org.dhruv8sh.kara" ] || kpkg Plasma/Applet "$R/third-party/org.dhruv8sh.kara"
[ -d "$HOME/.local/share/icons/Papirus-Ito" ] || { step "Icons: building greyscale Papirus-Ito"; "$R/scripts/make-icons.sh"; }

step "Konsole + Yakuake"
mkdir -p "$HOME/.local/share/konsole"
cp "$R/themes/konsole/JunjiIto.colorscheme" "$R/themes/konsole/JunjiIto.profile" "$HOME/.local/share/konsole/"
# the colour scheme gets the faint spiral as a terminal wallpaper
kw --file "$HOME/.local/share/konsole/JunjiIto.colorscheme" --group General --key Wallpaper "$D/term-bg.png"
kw --file konsolerc --group "Desktop Entry" --key DefaultProfile JunjiIto.profile
kw --file yakuakerc --group "Desktop Entry" --key DefaultProfile JunjiIto.profile
kw --file yakuakerc --group Window --key Height 55
kw --file yakuakerc --group Window --key Width 80
kw --file yakuakerc --group Window --key KeepOpen false
kw --file yakuakerc --group Appearance --key Translucency true
kw --file yakuakerc --group Animation --key Frames 22

step "Terminals and shell: alacritty, kitty, fish, fastfetch, cava"
for c in alacritty kitty fish fastfetch cava; do
  p="$CFG/$c"
  # yours were symlinks into a deleted /tmp folder: replace those with real folders
  if [ -L "$p" ] && [ ! -e "$p" ]; then rm "$p"; fi
  mkdir -p "$p"
done
cp "$R/themes/alacritty/alacritty.toml" "$CFG/alacritty/alacritty.toml"
sed "s#~/.local/share/junji-ito-rice#$D#" "$R/themes/kitty/kitty.conf" > "$CFG/kitty/kitty.conf"
mkdir -p "$CFG/fish/functions"
cp "$R/themes/fish/config.fish" "$CFG/fish/config.fish"
cp "$R"/themes/fish/functions/*.fish "$CFG/fish/functions/"
cp "$R/themes/fastfetch/config.jsonc" "$R/themes/fastfetch/spiral.txt" "$CFG/fastfetch/"
cp "$R/themes/cava/config" "$CFG/cava/config"

step "GTK apps (adw-gtk3 / libadwaita palette, icons, font)"
for v in 3.0 4.0; do
  mkdir -p "$CFG/gtk-$v"
  cp "$R/themes/gtk/junji-ito.css" "$CFG/gtk-$v/junji-ito.css"
  printf '@import url("junji-ito.css");\n' > "$CFG/gtk-$v/gtk.css"
  kw --file "$CFG/gtk-$v/settings.ini" --group Settings --key gtk-icon-theme-name Papirus-Ito
  kw --file "$CFG/gtk-$v/settings.ini" --group Settings --key gtk-font-name "Zen Old Mincho Medium 10"
  kw --file "$CFG/gtk-$v/settings.ini" --group Settings --key gtk-application-prefer-dark-theme true
done

step "Plasma: colors, icons, fonts, cursor, splash, lock screen"
# a black accent colour would override the scheme's paper-white highlight
kw --file kdeglobals --group General --key AccentColor --delete
kw --file kdeglobals --group General --key LastUsedCustomAccentColor --delete
plasma-apply-colorscheme JunjiIto >/dev/null || true
/usr/lib/plasma-changeicons Papirus-Ito >/dev/null 2>&1 || kw --file kdeglobals --group Icons --key Theme Papirus-Ito
plasma-apply-cursortheme Bibata-Modern-Ice >/dev/null 2>&1 || true
plasma-apply-desktoptheme default >/dev/null 2>&1 || true
UI="Zen Old Mincho,10,-1,5,500,0,0,0,0,0,0,0,0,0,0,1"
kw --file kdeglobals --group General --key font "$UI"
kw --file kdeglobals --group General --key menuFont "$UI"
kw --file kdeglobals --group General --key toolBarFont "$UI"
kw --file kdeglobals --group General --key smallestReadableFont "Zen Old Mincho,9,-1,5,500,0,0,0,0,0,0,0,0,0,0,1"
kw --file kdeglobals --group General --key fixed "JetBrainsMono Nerd Font,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
kw --file kdeglobals --group WM --key activeFont "Shippori Mincho B1,10,-1,5,600,0,0,0,0,0,0,0,0,0,0,1"
kw --file kdeglobals --group KDE --key LookAndFeelPackage org.junjiito.desktop
kw --file kdeglobals --group KDE --key widgetStyle Breeze
kw --file ksplashrc --group KSplash --key Engine KSplashQML
kw --file ksplashrc --group KSplash --key Theme org.junjiito.desktop
kw --file kscreenlockerrc --group Greeter --key WallpaperPlugin org.kde.image
kw --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General --key Image "file://$D/tomie-still.png"
kw --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General --key PreviewImage "file://$D/tomie-still.png"

step "KWin: Junji Ito decoration (spiral close, eye buttons), effects"
kw --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae.v2
kw --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__JunjiIto
kw --file kwinrc --group org.kde.kdecoration2 --key BorderSize Tiny
kw --file kwinrc --group org.kde.kdecoration2 --key BorderSizeAuto false
kw --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft MFS
kw --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight IAX
kw --file kwinrc --group Plugins --key diminactiveEnabled true
kw --file kwinrc --group Effect-diminactive --key Strength 25
kw --file kwinrc --group Effect-cube --key Background Color
kw --file kwinrc --group Effect-cube --key BackgroundColor 0,0,0
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true

step "Visualizer toggle (button in the panel, Meta+Shift+V)"
install -Dm755 "$R/scripts/bin/junji-visualizer" "$HOME/.local/bin/junji-visualizer"
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/junji-visualizer-toggle.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Uzumaki Visualizer
Comment=Show or hide the vertical audio waves on the desktop
Exec=$HOME/.local/bin/junji-visualizer toggle
Icon=$D/junji-visualizer.svg
Terminal=false
Categories=AudioVideo;Audio;
X-KDE-Shortcuts=Meta+Shift+V
EOF
kw --file kglobalshortcutsrc --group services --group junji-visualizer-toggle.desktop --key _launch "Meta+Shift+V"
# also tell the running shortcut daemon, otherwise it rewrites the file without our entry
VIS_ID="['junji-visualizer-toggle.desktop', '_launch', 'Uzumaki Visualizer', 'Uzumaki Visualizer']"
VIS_KEY=$((0x10000000 | 0x02000000 | 0x56))   # Meta+Shift+V
gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel \
  --method org.kde.KGlobalAccel.doRegister "$VIS_ID" >/dev/null 2>&1 &&
gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel \
  --method org.kde.KGlobalAccel.setForeignShortcutKeys "$VIS_ID" "[([$VIS_KEY,0,0,0],)]" >/dev/null 2>&1 || true

step "Desktop (Tomie video wallpaper, Ito Clock) and panel"
PC_JSON=$(python3 "$R/scripts/make-panel-preset.py")
JS=$(python3 - "$R/scripts/plasma-layout.js" "$HOME" "$PC_JSON" <<'PY'
import sys
js = open(sys.argv[1]).read()
print(js.replace("__HOME__", sys.argv[2]).replace("__PANEL_COLORIZER_JSON__", sys.argv[3]))
PY
)
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$JS"

step "Done"
echo "Log out and back in once so every app picks up the new fonts, icons and decoration."
