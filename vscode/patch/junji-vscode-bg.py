#!/usr/bin/env python3
"""Inject the Junji Ito background into VS Code's workbench CSS.

  junji-vscode-bg apply  [--root DIR] [--share DIR]
  junji-vscode-bg remove [--root DIR]

Adds a marked block to workbench.desktop.main.css (images embedded as data URIs)
and rewrites that file's checksum in product.json so VS Code does not
complain that the installation is corrupt. Safe to run repeatedly; a pacman hook
runs `apply` after every visual-studio-code-bin upgrade.
"""
import argparse
import base64
import hashlib
import json
import pathlib
import re
import sys

START, END = "/* junji-ito-rice:start */", "/* junji-ito-rice:end */"
CSS_KEY = "vs/workbench/workbench.desktop.main.css"


def data_uri(path: pathlib.Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def strip_block(css: str) -> str:
    return re.sub(r"\n?" + re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", css, flags=re.S)


def update_checksum(app: pathlib.Path, css_bytes: bytes) -> None:
    product = app / "product.json"
    raw = product.read_text()
    data = json.loads(raw)
    if CSS_KEY not in data.get("checksums", {}):
        return
    new = base64.b64encode(hashlib.sha256(css_bytes).digest()).decode().rstrip("=")
    old = data["checksums"][CSS_KEY]
    # textual replace keeps product.json formatting byte-identical otherwise
    product.write_text(raw.replace(f'"{old}"', f'"{new}"', 1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["apply", "remove"])
    ap.add_argument("--root", default="/usr/share/code", help="VS Code install dir")
    ap.add_argument("--share", default="/usr/local/share/junji-ito-rice/vscode", help="dir with junji.css + images")
    a = ap.parse_args()

    app = pathlib.Path(a.root) / "resources/app"
    css_file = app / "out" / CSS_KEY
    if not css_file.exists():
        print(f"junji-vscode-bg: {css_file} not found", file=sys.stderr)
        return 1

    css = strip_block(css_file.read_text())
    if a.action == "apply":
        share = pathlib.Path(a.share)
        block = (share / "junji.css").read_text()
        for img in share.glob("*.png"):
            block = block.replace("@" + img.stem.upper().replace("-", "_") + "@", data_uri(img))
        css = css.rstrip("\n") + "\n" + START + "\n" + block.strip() + "\n" + END + "\n"

    css_file.write_text(css)
    update_checksum(app, css.encode())
    print(f"junji-vscode-bg: {a.action} done ({css_file}). Restart VS Code fully to see it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
