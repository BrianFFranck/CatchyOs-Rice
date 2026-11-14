#!/usr/bin/env bash
# Junji Ito rice: configure the plugins installed by install-system.sh (runs as you, in your session).
set -uo pipefail
cd "$(dirname "$0")/.."
R=$PWD
kw() { kwriteconfig6 "$@"; }
have_effect() { ls /usr/share/kwin/effects /usr/lib/qt6/plugins/kwin/effects/plugins 2>/dev/null | grep -q "$1"; }

# --- KDE Rounded Corners: small radius + 1px manga-panel outline matching the decoration
if have_effect shapecorners; then
  echo "  rounded corners"
  G=(--file kwinrc --group Round-Corners)
  kw "${G[@]}" --key Size 8
  kw "${G[@]}" --key InactiveCornerRadius 8
  kw "${G[@]}" --key UseSquircleShape false
  kw "${G[@]}" --key OutlineThickness 1
  kw "${G[@]}" --key InactiveOutlineThickness 1
  kw "${G[@]}" --key OutlineColor 217,215,210
  kw "${G[@]}" --key InactiveOutlineColor 38,38,38
  kw "${G[@]}" --key ActiveOutlineUseCustom true
  kw "${G[@]}" --key InactiveOutlineUseCustom true
  kw "${G[@]}" --key SecondOutlineThickness 0
  kw "${G[@]}" --key InactiveSecondOutlineThickness 0
  kw "${G[@]}" --key ActiveShadowAlpha 160
  kw "${G[@]}" --key InactiveShadowAlpha 90
  kw "${G[@]}" --key DisableRoundMaximize true
  kw "${G[@]}" --key DisableOutlineMaximize true
  kw "${G[@]}" --key DisableRoundFullScreen true
  kw "${G[@]}" --key DisableOutlineFullScreen true
  kw --file kwinrc --group Plugins --key kwin4_effect_shapecornersEnabled true
fi

# --- Burn My Windows: TV-glitch open/close in paper white (replaces Kinetic scale)
TV=$(ls /usr/share/kwin/effects 2>/dev/null | grep -E '_effect_tv_glitch$' | head -1)
if [ -n "$TV" ]; then
  echo "  burn my windows: $TV"
  kw --file kwinrc --group Plugins --key "${TV}Enabled" true
  kw --file kwinrc --group Plugins --key kinetic_scaleEnabled false
  kw --file kwinrc --group "Effect-$TV" --key Color "#d9d7d2"
  kw --file kwinrc --group "Effect-$TV" --key Duration 520
  kw --file kwinrc --group "Effect-$TV" --key Strength 2
fi

# --- Polonium is installed but stays OFF: Krohnkite is already your tiler and the two fight.
kw --file kwinrc --group Plugins --key poloniumEnabled false

qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true

# --- CopyQ: ink theme, autostart
if command -v copyq >/dev/null; then
  echo "  copyq"
  mkdir -p "$HOME/.config/copyq/themes"
  cp "$R/themes/copyq/JunjiIto.ini" "$HOME/.config/copyq/themes/"
  (copyq --start-server >/dev/null 2>&1 &) ; sleep 2
  copyq loadTheme "$HOME/.config/copyq/themes/JunjiIto.ini" >/dev/null 2>&1 || true
  copyq config autostart true >/dev/null 2>&1 || true
fi

# --- Yakuake drop-down terminal (F12) starts with the session
if [ -f /usr/share/applications/org.kde.yakuake.desktop ]; then
  mkdir -p "$HOME/.config/autostart"
  cp /usr/share/applications/org.kde.yakuake.desktop "$HOME/.config/autostart/"
  pgrep -x yakuake >/dev/null || (setsid yakuake >/dev/null 2>&1 &)
fi

# --- the twin vertical waves
if kpackagetool6 -t Plasma/Applet -l 2>/dev/null | grep -qx luisbocanegra.audio.visualizer; then
  echo "  visualizer: $("$HOME/.local/bin/junji-visualizer" on)"
fi
