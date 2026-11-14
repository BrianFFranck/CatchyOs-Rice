#!/usr/bin/env python3
"""Build the 'Junji Ito' Panel Colorizer preset from the stock 'Black Gray Lines' preset.

Ink-black floating panel with a 1px grey frame (a manga panel border), paper-white
widget text and a faint underline under each widget.
Writes ~/.config/panel-colorizer/presets/Junji Ito/settings.json and prints the
compact JSON (used as the widget's globalSettings).
"""
import copy
import json
import os

BASE = "/usr/share/plasma/plasmoids/luisbocanegra.panel.colorizer/contents/ui/presets/Black Gray Lines/settings.json"
OUT_DIR = os.path.expanduser("~/.config/panel-colorizer/presets/Junji Ito")

with open(BASE) as f:
    preset = json.load(f)
g = preset["globalSettings"]


def color(c, custom, alpha=1.0):
    c.update({"enabled": True, "sourceType": 0, "custom": custom, "alpha": alpha})


panel = g["panel"]["normal"]
color(panel["backgroundColor"], "#050505", 0.94)
panel["radius"]["enabled"] = True
panel["radius"]["corner"] = {k: 6 for k in ("topLeft", "topRight", "bottomRight", "bottomLeft")}
panel["border"].update({"enabled": True, "customSides": False, "width": 1})
color(panel["border"]["color"], "#383838")
panel["shadow"]["background"].update({"enabled": True, "size": 14, "xOffset": 0, "yOffset": 2})
color(panel["shadow"]["background"]["color"], "#000000", 0.85)

widgets = g["widgets"]["normal"]
color(widgets["foregroundColor"], "#d9d7d2")
widgets["border"].update({"enabled": True, "customSides": True})
widgets["border"]["custom"]["widths"] = {"left": 0, "bottom": 1, "right": 0, "top": 0}
color(widgets["border"]["color"], "#3a3a3a")
widgets["spacing"] = 6

tray = g["trayWidgets"]["normal"]
tray["enabled"] = True
color(tray["foregroundColor"], "#bdbbb6")

sp = g["stockPanelSettings"]
sp["floating"] = {"enabled": True, "value": True}
sp["thickness"] = {"enabled": True, "value": 40}
sp["position"] = {"enabled": True, "value": "bottom"}

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "settings.json"), "w") as f:
    json.dump(preset, f, indent=4)
print(json.dumps(g, separators=(",", ":")))
