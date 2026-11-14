#!/usr/bin/env python3
"""Pack vscode/theme/ into a .vsix (no npm/vsce needed) and print its path.

Usage: python3 vscode/build-theme-vsix.py && code --install-extension vscode/junji-ito-theme.vsix --force
"""
import json
import pathlib
import zipfile

here = pathlib.Path(__file__).resolve().parent
src = here / "theme"
pkg = json.loads((src / "package.json").read_text())
out = here / f"{pkg['name']}.vsix"

manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="{pkg['name']}" Version="{pkg['version']}" Publisher="{pkg['publisher']}"/>
    <DisplayName>{pkg['displayName']}</DisplayName>
    <Description xml:space="preserve">{pkg['description']}</Description>
    <Categories>Themes</Categories>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{pkg['engines']['vscode']}"/>
    </Properties>
  </Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
  </Assets>
</PackageManifest>
"""
content_types = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".json" ContentType="application/json"/>
  <Default Extension=".vsixmanifest" ContentType="text/xml"/>
</Types>
"""

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("extension.vsixmanifest", manifest)
    z.writestr("[Content_Types].xml", content_types)
    for f in sorted(src.rglob("*")):
        if f.is_file():
            z.write(f, "extension/" + f.relative_to(src).as_posix())
print(out)
