#!/usr/bin/env bash
# Put the Uzumaki girl behind your code in VS Code (visual-studio-code-bin).
#   sudo ./install-vscode-bg.sh            install + apply (also installs uv)
#   sudo ./install-vscode-bg.sh --remove   undo everything
# A pacman hook re-applies the patch automatically after every VS Code update.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "run with sudo: sudo $0 $*"; exit 1; }

here="$(cd "$(dirname "$0")" && pwd)"
share=/usr/local/share/junji-ito-rice/vscode
bin=/usr/local/bin/junji-vscode-bg
hook=/etc/pacman.d/hooks/90-junji-vscode-bg.hook

if [[ "${1:-}" == "--remove" ]]; then
    [[ -x $bin ]] && "$bin" remove || true
    rm -f "$hook" "$bin"
    rm -rf "$share"
    echo "removed. Restart VS Code."
    exit 0
fi

install -Dm755 "$here/patch/junji-vscode-bg.py" "$bin"
install -Dm644 "$here/patch/junji.css" "$share/junji.css"
install -Dm644 "$here/assets/uzumaki-ghost.png" "$share/uzumaki-ghost.png"
install -Dm644 /dev/stdin "$hook" <<'EOF'
[Trigger]
Operation = Install
Operation = Upgrade
Type = Package
Target = visual-studio-code-bin

[Action]
Description = Re-applying Junji Ito background to VS Code...
When = PostTransaction
Exec = /usr/local/bin/junji-vscode-bg apply
EOF

"$bin" apply

# uv: fast Python project/venv manager (official repo)
pacman -S --needed --noconfirm uv

echo
echo "done. Close ALL VS Code windows and open it again."
