#!/usr/bin/env bash
# Junji Ito rice: the parts that need root.
#   packages · GRUB theme · Plymouth boot splash · login screen (noctalia-greeter) · TTY colours
# Run it as YOUR user (not with sudo): it asks for your password when it needs it.
set -uo pipefail
if [ "$EUID" -eq 0 ]; then echo "Run this as your normal user, without sudo." >&2; exit 1; fi
cd "$(dirname "$0")/.."
R=$PWD
SB=/var/backups/junji-ito-rice
step() { printf '\n\033[97m꩜ %s\033[0m\n' "$*"; }
warn() { printf '\033[91m  ! %s\033[0m\n' "$*"; }
FAILED=()

sudo -v || exit 1
sudo mkdir -p "$SB"
# keep sudo alive for the AUR builds
while true; do sudo -n true; sleep 50; kill -0 "$$" || exit; done 2>/dev/null &

# ------------------------------------------------------------------ packages
step "Repo packages: cava, CopyQ, websockets (visualizer backend), Spectacle"
sudo pacman -S --needed --noconfirm cava copyq qt6-websockets python-websockets spectacle \
  fish kitty alacritty fastfetch yakuake filelight ttf-jetbrains-mono-nerd papirus-icon-theme \
  python-numpy python-scipy python-opencv ffmpeg imagemagick git \
  || FAILED+=("pacman packages")

step "AUR packages (each one is built separately, so one failure does not stop the rest)"
AUR=(
  plasma6-applets-audio-visualizer   # vertical wave visualizer (cava)
  kwin-effect-rounded-corners        # KDE Rounded Corners
  kwin-polonium                      # Polonium tiling (installed, left OFF: you use Krohnkite)
  plasmazones-bin                    # Plasma Zones (FancyZones-style snapping)
  kwin-effects-burn-my-windows       # Burn My Windows: TV-glitch open/close animation
  kwin-scripts-krohnkite-git         # Krohnkite tiling (the one you actually use)
  plasma6-applets-panel-colorizer    # Panel Colorizer: the floating/transparent ink panel
  kwin-effects-better-blur-dx        # blur behind popups
  plasma6-wallpapers-smart-video-wallpaper-reborn   # fallback video wallpaper (remove-haunted.sh)
)
for p in "${AUR[@]}"; do
  echo "  → $p"
  yay -S --needed --noconfirm --answerclean None --answerdiff None --removemake "$p" \
    || { warn "$p failed to build/install"; FAILED+=("$p"); }
done

# ------------------------------------------------------------------ fonts + cursor for the login screen
step "Fonts and cursor where the login screen can see them"
sudo install -Dm644 -t /usr/local/share/fonts/junji-ito "$HOME"/.local/share/fonts/junji-ito/*.ttf
sudo fc-cache -f /usr/local/share/fonts >/dev/null
if [ -d "$HOME/.local/share/icons/Bibata-Modern-Ice" ] && [ ! -d /usr/share/icons/Bibata-Modern-Ice ]; then
  sudo cp -r "$HOME/.local/share/icons/Bibata-Modern-Ice" /usr/share/icons/
fi

# ------------------------------------------------------------------ GRUB
step "GRUB: Uzumaki theme"
[ -f "$SB/grub.default" ] || sudo cp /etc/default/grub "$SB/grub.default"
sudo rm -rf /usr/share/grub/themes/junji-ito
sudo cp -r "$R/themes/grub/junji-ito" /usr/share/grub/themes/
sudo sed -i 's|^#\?GRUB_THEME=.*|GRUB_THEME="/usr/share/grub/themes/junji-ito/theme.txt"|' /etc/default/grub
sudo sed -i 's|^GRUB_GFXMODE=.*|GRUB_GFXMODE=1920x1080,auto|' /etc/default/grub
# TTY / console colours: same ink-and-paper palette as the terminals
if ! grep -q 'vt.default_red' /etc/default/grub; then
  VT=$(python3 - <<'PY'
pal = ["101010","8f1d1d","8a8a8a","a39d8c","6e6e6e","7d6f6f","9aa0a0","c8c6c1",
       "464646","b52a2a","b0b0b0","c9c3b2","9a9a9a","a39494","c2c8c8","f2f0eb"]
ch = lambda i: ",".join(str(int(c[i:i+2], 16)) for c in pal)
print(f"vt.default_red={ch(0)} vt.default_grn={ch(2)} vt.default_blu={ch(4)}")
PY
)
  sudo sed -i -E "s|^(GRUB_CMDLINE_LINUX_DEFAULT=['\"])(.*)(['\"])$|\1\2 $VT\3|" /etc/default/grub
fi
grep -E '^GRUB_(THEME|GFXMODE|CMDLINE_LINUX_DEFAULT)=' /etc/default/grub
sudo grub-mkconfig -o /boot/grub/grub.cfg || FAILED+=("grub-mkconfig")

# ------------------------------------------------------------------ Plymouth
step "Plymouth: Uzumaki boot splash"
[ -f "$SB/plymouth.theme" ] || plymouth-set-default-theme | sudo tee "$SB/plymouth.theme" >/dev/null
sudo rm -rf /usr/share/plymouth/themes/junji-ito
sudo cp -r "$R/themes/plymouth/junji-ito" /usr/share/plymouth/themes/
sudo plymouth-set-default-theme junji-ito
echo "  rebuilding initramfs (takes a minute)…"
sudo mkinitcpio -P >/dev/null || FAILED+=("mkinitcpio")
echo "  plymouth theme: $(plymouth-set-default-theme)"

# ------------------------------------------------------------------ login screen
step "Login screen (noctalia-greeter): Uzumaki wallpaper, ink palette, mincho fonts"
GDIR=/var/lib/noctalia-greeter
if sudo test -d "$GDIR"; then
  OWNER=$(sudo stat -c '%U:%G' "$GDIR")
  sudo test -f "$SB/greeter.toml" || { sudo test -f "$GDIR/greeter.toml" && sudo cp "$GDIR/greeter.toml" "$SB/greeter.toml" || sudo touch "$SB/greeter.toml.absent"; }
  sudo install -m644 "$R/assets/uzumaki-login.png" "$GDIR/junji-ito.png"
  sudo python3 -I - "$GDIR/greeter.toml" <<'PY'
import json, os, sys, tomllib
p = sys.argv[1]
data = tomllib.load(open(p, "rb")) if os.path.exists(p) else {}
ap = data.setdefault("appearance", {})
ap.update(scheme="Synced", theme_mode="dark", corner_radius_scale=0.35,
          font_family="Zen Old Mincho", hide_logo=True, password_style="default",
          scheme_selector_position="hidden")
ap["palette"] = {
    "primary": "#e4e2dd", "on_primary": "#050505",
    "secondary": "#8a8a8a", "on_secondary": "#050505",
    "tertiary": "#a51d1d", "on_tertiary": "#f2f0eb",
    "error": "#b52a2a", "on_error": "#f2f0eb",
    "surface": "#050505", "on_surface": "#e4e2dd",
    "surface_variant": "#111111", "on_surface_variant": "#7a7a7a",
    "outline": "#2a2a2a", "shadow": "#000000",
    "hover": "#e4e2dd", "on_hover": "#050505",
}
ap["wallpaper"] = {"path": "/var/lib/noctalia-greeter/junji-ito.png", "fill_mode": "crop",
                   "fill_color": "#000000"}
data.setdefault("clock", {}).update(enabled=True, position="above-panel", time_format="{:%H:%M}",
                                    date_format="%A  ·  %d %B")
for k in ("time_font_size", "date_font_size"):  # not supported by noctalia-greeter 1.7
    data["clock"].pop(k, None)
data.setdefault("cursor", {}).update(theme="Bibata-Modern-Ice", size=24)

def val(v):
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return repr(v)
    if isinstance(v, list): return "[" + ", ".join(val(x) for x in v) + "]"
    if isinstance(v, dict): return "{ " + ", ".join(f"{json.dumps(k)} = {val(x)}" for k, x in v.items()) + " }"
    return json.dumps(v, ensure_ascii=False)

out = []
def dump(d, path):
    scal = {k: v for k, v in d.items() if not isinstance(v, dict)}
    tabs = {k: v for k, v in d.items() if isinstance(v, dict)}
    if path and scal:
        out.append(f"[{'.'.join(path)}]")
    for k, v in scal.items():
        out.append(f"{k} = {val(v)}")
    if scal: out.append("")
    for k, v in tabs.items():
        if not any(not isinstance(x, dict) for x in v.values()) and not v:
            out.append(f"[{'.'.join(path + [k])}]"); out.append("")
        dump(v, path + [k])
dump(data, [])
open(p, "w").write("# Junji Ito rice: appearance merged into your existing settings\n" + "\n".join(out))
PY
  sudo chown "$OWNER" "$GDIR/greeter.toml" "$GDIR/junji-ito.png"
  sudo cat "$GDIR/greeter.toml" | sed 's/^/    /' | head -50
else
  warn "noctalia-greeter state dir not found; login screen not themed"
fi

# ------------------------------------------------------------------ plugin configuration (as you)
step "Configuring the new plugins in your session"
"$R/scripts/configure-plugins.sh" || FAILED+=("configure-plugins")

step "Finished"
if [ ${#FAILED[@]} -gt 0 ]; then
  warn "Some steps failed: ${FAILED[*]}"
  warn "Everything else is installed. Re-running this script retries only what is missing."
else
  echo "Everything installed. Reboot to see GRUB → Plymouth → login → desktop."
fi
