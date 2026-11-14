#!/usr/bin/env bash
# Undo the Junji Ito rice.
#   restore.sh            your desktop configs go back to exactly how they were before the rice
#   restore.sh --system   also reverts GRUB, Plymouth and the login screen (asks for your password)
# Note: config changes you made yourself *after* installing the rice are rolled back too.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/files.list.sh"
ROOT="$HOME/.local/share/junji-ito-rice/backups"
B=$(cat "$ROOT/ORIGINAL" 2>/dev/null) || { echo "No original backup found in $ROOT" >&2; exit 1; }
echo "Restoring from $B"

# safety net: snapshot the riced state too, in case you want it back
"$HERE/backup.sh" >/dev/null

cd "$HOME"
for f in "${FILES[@]}"; do
  if [ -e "$B/$f" ] || [ -L "$B/$f" ]; then
    rm -rf "$f"
    mkdir -p "$(dirname "$f")"
    cp -aP "$B/$f" "$f"
  elif grep -qxF "$f" "$B/ABSENT" 2>/dev/null; then
    rm -rf "$f"          # did not exist before the rice
  fi
done
rm -rf "$HOME/.config/panel-colorizer/presets/Junji Ito"

# re-apply the restored look
SCHEME=$(kreadconfig6 --file kdeglobals --group General --key ColorScheme)
[ -n "$SCHEME" ] && plasma-apply-colorscheme "$SCHEME" >/dev/null 2>&1
ICONS=$(kreadconfig6 --file kdeglobals --group Icons --key Theme)
/usr/lib/plasma-changeicons "${ICONS:-breeze}" >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
systemctl --user restart plasma-plasmashell.service 2>/dev/null || { kquitapp6 plasmashell; (setsid plasmashell >/dev/null 2>&1 &); }
echo "Desktop restored. Log out and back in to finish."

if [ "${1:-}" = "--system" ]; then
  SB=/var/backups/junji-ito-rice
  sudo -v || exit 1
  if sudo test -f "$SB/grub.default"; then
    sudo cp "$SB/grub.default" /etc/default/grub && sudo grub-mkconfig -o /boot/grub/grub.cfg
  fi
  if sudo test -f "$SB/plymouth.theme"; then
    sudo plymouth-set-default-theme "$(sudo cat "$SB/plymouth.theme")" && sudo mkinitcpio -P >/dev/null
  fi
  G=/var/lib/noctalia-greeter
  if sudo test -f "$SB/greeter.toml"; then
    sudo cp "$SB/greeter.toml" "$G/greeter.toml"
  elif sudo test -f "$SB/greeter.toml.absent"; then
    sudo rm -f "$G/greeter.toml"
  fi
  sudo rm -f "$G/junji-ito.png"
  echo "GRUB, Plymouth and login screen restored. Packages were left installed."
fi
