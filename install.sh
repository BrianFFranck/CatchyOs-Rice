#!/usr/bin/env bash
# CatchyOs Rice: one command on a fresh CachyOS + KDE Plasma 6 install.
#   ./install.sh              everything (asks for your sudo password once)
#   ./install.sh --no-system  only your home folder (no packages, GRUB, Plymouth, login screen)
# Run it from a Plasma session (not a TTY), as your normal user. Safe to re-run.
set -uo pipefail
cd "$(dirname "$0")"
R=$PWD
say() { printf '\n\033[97m꩜ %s\033[0m\n' "$*"; }
die() { printf '\033[91m%s\033[0m\n' "$*" >&2; exit 1; }

[ "$EUID" -eq 0 ] && die "Run this as your normal user, without sudo."
command -v plasmashell >/dev/null || die "KDE Plasma 6 is needed (plasmashell not found)."
[ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ] || die "Run this from inside your Plasma session (open Konsole), not a TTY."
SYSTEM=1; [ "${1:-}" = "--no-system" ] && SYSTEM=0

if [ $SYSTEM = 1 ]; then
  say "1/5  System: packages, GRUB, Plymouth, login screen (asks for your password)"
  command -v yay >/dev/null || sudo pacman -S --needed --noconfirm yay || die "yay is needed for AUR packages."
  "$R/scripts/install-system.sh" || echo "  (some system steps failed; the rest continues; re-run later to retry)"
fi

say "2/5  Your desktop: fonts, icons, colours, window frames, terminals, panel"
"$R/scripts/install-user.sh" || die "install-user.sh failed (see above)."

say "3/5  Plugins (rounded corners, visualizer, Krohnkite, ...)"
"$R/scripts/configure-plugins.sh" || true

say "4/5  Haunted desktops: 5 animated wallpapers, Plasma Style, sounds, spiral close"
"$R/scripts/install-haunted.sh" || die "install-haunted.sh failed (see above)."

say "5/5  VS Code (only if it is installed)"
if command -v code >/dev/null; then
  code --install-extension "$R/vscode/junji-ito-theme.vsix" --force >/dev/null && echo "  theme installed (pick 'Junji Ito' in Ctrl+K Ctrl+T)"
  if [ $SYSTEM = 1 ]; then sudo "$R/vscode/install-vscode-bg.sh" || true; fi
else
  echo "  VS Code not found, skipped (run this script again after installing it)"
fi

say "Done. Log out and back in (or reboot to see the Uzumaki boot screen)."
