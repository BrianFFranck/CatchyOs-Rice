#!/usr/bin/env bash
# Snapshot every config the Junji Ito rice touches, so restore.sh can put it all back.
# Paths that do not exist yet are listed in ABSENT (restore removes only those).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/files.list.sh"
ROOT="$HOME/.local/share/junji-ito-rice/backups"
DEST="$ROOT/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DEST"
cd "$HOME"
: > "$DEST/ABSENT"
for f in "${FILES[@]}"; do
  if [ -e "$f" ] || [ -L "$f" ]; then
    # -P keeps symlinks as symlinks (some of yours pointed into a deleted /tmp folder)
    cp -aP --parents "$f" "$DEST/" 2>/dev/null || true
  else
    echo "$f" >> "$DEST/ABSENT"
  fi
done
echo "$DEST" > "$ROOT/LATEST"
# the very first backup is your pre-rice setup: restore.sh goes back to that one
[ -f "$ROOT/ORIGINAL" ] || echo "$DEST" > "$ROOT/ORIGINAL"
echo "Backup saved to $DEST"
