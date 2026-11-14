# ꩜ Junji Ito: a CachyOS KDE Plasma rice

> The long version. For a quick start see the [main README](../README.md).

Ink black, manga-paper white, grey, and one drop of dried blood.
**Tomie** lives on the desktop (looping video); **Uzumaki** greets you at boot.

## What changes

| Area | What you get |
|---|---|
| Desktop | 16 s seamless loop: Tomie with a slowly turning Uzumaki spiral behind her. The fake face she holds is alive: it breathes and gapes on its own, its eyes roll up white, circle and dart, and it slowly peels away from her cheek with threads of skin stretching across the tear, then snaps back on during the glitch. Tomie breathes too. Also film grain, candle flicker, an occasional glitch twitch, and 富江 / 何度でも蘇る ("returns again and again") in brush script. Pauses behind maximized windows and on low battery. |
| Lock screen | Tomie still frame |
| Boot | GRUB menu with Uzumaki art and a typewriter menu → Plymouth splash where the Uzumaki art fades out of the dark over a turning spiral |
| Login | noctalia-greeter: Uzumaki wallpaper, ink palette, mincho font (your existing settings are kept) |
| KDE splash | Turning spiral, 富江 and typewritten lines as Plasma loads |
| Colors | `Junji Ito` scheme: inverted (paper-white) selections, blood red only for errors |
| Window frames | Custom Aurorae theme: 1px manga-panel outline. Close = **spiral** (turns red on hover), maximize = **open eye**, restore = **half-open eye**, minimize = **closed eye** |
| Icons | **Papirus-Ito**: all ~44k Papirus icons converted to greyscale |
| Fonts | Zen Old Mincho (UI), Shippori Mincho B1 (titles), Yuji Syuku (brush), Special Elite (typewriter), JetBrainsMono Nerd Font (terminal) |
| Panel | Floating ink panel (Panel Colorizer): spiral launcher, **Ito Eye**, Kara pager, centered task icons, visualizer button, **Ito Vitals**, tray, mincho clock |
| Widgets | **Ito Vitals**: CPU, temperature (熱), RAM and network speed in typewriter type with thin ink gauges; they turn blood red and breathe when the laptop runs hot. Click for pen-line history, GPU, disk, fan and a btop button. Right-click → Configure to pick what shows. **Ito Eye**: wanders, blinks, watches your cursor, flinches when clicked. **Ito Clock**: brush-script time, kanji date, a line that changes every 15 min |
| Visualizer | Two **vertical** audio waves along the left and right screen edges. Toggle with the panel button or **Meta+Shift+V**, or run `junji-visualizer on/off` |
| Terminals | Alacritty, Kitty, Konsole and Yakuake share one palette. Kitty and Konsole have a faint spiral in the corner |
| Shell | fish: `╭─ ꩜ path ⟡ branch` prompt (the arrow bleeds red on errors), Uzumaki fastfetch, a random line from the Ito universe. `ito` prints another; `spiral` opens cava |
| TTY | The console (Ctrl+Alt+F3) uses the same palette |
| Effects | Dim inactive, KDE Rounded Corners with a matching outline, Burn My Windows TV-glitch open/close in paper white |
| Extras | CopyQ (ink theme, autostart), Filelight, Yakuake (F12, autostart), Polonium (installed but **off**), Plasma Zones |

## Haunted desktops (add-on)

Five virtual desktops, each with its own living wallpaper (`org.junjiito.wallpaper` plugin):

| Desktop | Wallpaper |
|---|---|
| 1 富江 Tomie | the original Tomie loop |
| 2 渦巻 Uzumaki | her hair spiral sinks into itself forever. The loop reuses the drawing's own ink (a phase field fitted to the rings, see `src/uzumaki/`). The eyeball in her hair rolls, and faint rings drift into her head |
| 3 地獄星 Remina | speech balloons removed with LaMa and the skyline rebuilt (`src/remina/`). The Hellstar breathes, its corona writhes and its pupil turns to look at her, then snaps shut while the panel flashes negative. A blood-red glow spills into space, her hair moves in the wind, and ash and embers rise from the city |
| 4 墨 Ink | a dry brush writes one spiral, the ink sinks in, then the wind takes it away as ash |
| 5 穴 Amigara | a torch searches a rock face full of human-shaped holes, then stops on yours |

* Switching desktops **soaks the next one in through an ink bleed**: from the right going forward, from the left going back. Every video runs on a shared clock, so a desktop has moved on while you were away.
* **The spiral spreads**: hand-inked spirals creep in from the screen edges the longer the machine stays up (from `/proc/uptime`; fully spread after 6 h, and a reboot clears them). To preview it, use Desktop → Configure → Wallpaper → *Preview spread*.
* Everything pauses behind maximized or fullscreen windows and below 15 % battery.
* **Plasma Style "Junji Ito"**: popups, notifications, KRunner and OSDs are ink-black manga panels with a double rule and screentone in the corners. The busy indicator is an Uzumaki spiral. The style carries its own ink palette, so it looks right whatever colour scheme your apps use.
* **Sound theme "Junji Ito"**, all synthesized (`scripts/gen-sounds.py`):
  * notifications: ink drips in a stone room
  * warnings: a creaking beam
  * errors: knocks and a beating low tone
  * low battery: a heartbeat
  * login and logout: a temple bowl over a drone
  * empty trash: crumpling paper
  * screenshots: an old shutter
* **KWin effect "Uzumaki"**: windows still open with the paper-white TV glitch, and now **close by winding into an inked spiral vortex**.

```sh
./scripts/build-desktops.sh          # (re)render the five videos (~6 min; LaMa only if assets/remina-clean.png is missing)
./scripts/install-haunted.sh         # install / re-apply (safe to re-run, does not touch the panel)
./scripts/remove-haunted.sh          # undo
```
To swap a desktop's wallpaper for any video or image: Desktop → Configure → Wallpaper → Desktop N.

## Install

```sh
# 1. Home-folder part (already done for you)
./scripts/install-user.sh

# 2. Root part: run in a real terminal (it asks for your password)
./scripts/install-system.sh

# 3. Log out and back in (or reboot to see GRUB + Plymouth)
```

`install-system.sh` can be re-run safely. If one AUR package fails to build, the rest still install.

## Notes

* **Polonium vs Krohnkite**: both are tiling scripts and they fight each other. You already use Krohnkite, so Polonium is installed but disabled. To switch:
  `kwriteconfig6 --file kwinrc --group Plugins --key krohnkiteEnabled false; kwriteconfig6 --file kwinrc --group Plugins --key poloniumEnabled true; qdbus6 org.kde.KWin /KWin reconfigure`
* **Plasma Zones** works alongside Krohnkite in *snapping* mode (hold Alt while dragging). Avoid its *tiling* mode while Krohnkite is on.
* **CopyQ vs the Plasma clipboard**: both keep history. You can remove the Clipboard entry from the tray if you prefer CopyQ.
* The animation is made by `scripts/animate-tomie.py` (timings are at the top of the file). The old still-portrait video is kept as `assets/tomie-loop-static.mp4`; to go back to it: `cp assets/tomie-loop-static.mp4 ~/.local/share/junji-ito-rice/tomie-loop.mp4 && systemctl --user restart plasma-plasmashell`.
* Rebuild the video or images (for example with a different picture): `TOMIE_SRC=/path/img.png ./scripts/build-assets.sh`, then re-run `install-user.sh`.

## VS Code

* **Theme** "Junji Ito" (`vscode/theme/`, same palette as the terminal). Rebuild/reinstall after edits:
  `python3 vscode/build-theme-vsix.py && code --install-extension vscode/junji-ito-theme.vsix --force`
* **Uzumaki girl behind the code**: `sudo vscode/install-vscode-bg.sh` patches VS Code's workbench CSS (image + typewriter tab labels from `vscode/patch/junji.css`) and fixes the checksum so there's no "corrupt installation" warning. A pacman hook (`/etc/pacman.d/hooks/90-junji-vscode-bg.hook`) re-applies it after every VS Code update. Change opacity/size in `junji.css`, then re-run the installer. Undo: `sudo vscode/install-vscode-bg.sh --remove`.
* Settings live in `~/dotfiles-cachyos/vscode/settings.json` (symlinked). Pre-change copy: `~/.config/Code/User/settings.json.bak-before-junji`.
* Python: default interpreter is the venv `~/.venvs/main` (numpy, pandas, matplotlib, requests, ipykernel, pytest, rich, python-dotenv). Ruff formats on save.

## Undo

```sh
./scripts/restore.sh            # desktop back to exactly how it was before
./scripts/restore.sh --system   # also GRUB, Plymouth and the login screen
```

Backups live in `~/.local/share/junji-ito-rice/backups/`. `ORIGINAL` points at your pre-rice setup. System backups are in `/var/backups/junji-ito-rice/`.

## Layout

```
assets/    generated video and images (scripts/build-assets.sh)
themes/    color scheme, aurorae, look-and-feel, plasmoids, grub, plymouth, terminals, gtk, copyq
scripts/   install-user.sh · install-system.sh · configure-plugins.sh · restore.sh · backup.sh
```
