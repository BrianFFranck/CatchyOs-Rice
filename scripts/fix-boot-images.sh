#!/usr/bin/env bash
# One-off fix (2026-11-08): reinstall the GRUB / Plymouth / login-screen images as
# 8-bit RGB PNGs. The 16-bit grayscale originals made GRUB print an error at boot
# and noctalia-greeter draw a garbled login screen. Run in your own terminal:
#   ~/Desktop/CLaudeTerminal/junji-ito-rice/scripts/fix-boot-images.sh
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
sudo -v

echo ">> GRUB theme images"
sudo install -m644 "$R"/themes/grub/junji-ito/*.png /usr/share/grub/themes/junji-ito/

echo ">> Login screen wallpaper"
GDIR=/var/lib/noctalia-greeter
OWNER=$(sudo stat -c '%U:%G' "$GDIR")
sudo install -m644 -o "${OWNER%%:*}" -g "${OWNER##*:}" "$R/assets/uzumaki-login.png" "$GDIR/junji-ito.png"
sudo sed -i -E '/^(time|date)_font_size = /d' "$GDIR/greeter.toml"

echo ">> Plymouth images + initramfs rebuild (takes a minute)"
sudo install -m644 "$R"/themes/plymouth/junji-ito/*.png /usr/share/plymouth/themes/junji-ito/
sudo mkinitcpio -P >/dev/null

echo
file /usr/share/grub/themes/junji-ito/background.png
sudo file "$GDIR/junji-ito.png"
echo "Done. Reboot to check the boot menu and login screen."
