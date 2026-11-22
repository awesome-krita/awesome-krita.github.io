#!/usr/bin/env python3
"""Copy the icons the site uses into site/app.js (the ICONS block).

python3 scripts/icons.py

To add an icon, add its Lucide name to LUCIDE and run this. Names: https://lucide.dev/icons
"""
import re
import urllib.request
from pathlib import Path

LUCIDE_VERSION = "0.460.0"  # Lucide, ISC license
SIMPLE_ICONS_VERSION = "13.21.0"  # Simple Icons, CC0
LUCIDE = ["download", "github", "plug", "palette", "brush", "wrench", "package", "tag", "scale", "star",
          "calendar", "monitor", "flag", "pencil"]
SIMPLE_ICONS = ["krita"]

APP = Path(__file__).resolve().parent.parent / "site" / "app.js"


def inner(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "awesome-krita"}), timeout=30) as r:
        svg = r.read().decode()
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S)[1]
    body = re.sub(r"<title>.*?</title>", "", body)
    return re.sub(r"\s*\n\s*", "", body).replace(" />", "/>").strip()


def main():
    lines = [f"  {n}: {{ stroke: true, d: '{inner(f'https://unpkg.com/lucide-static@{LUCIDE_VERSION}/icons/{n}.svg')}' }},"
             for n in LUCIDE]
    lines += [f"  {n}: {{ stroke: false, d: '{inner(f'https://unpkg.com/simple-icons@{SIMPLE_ICONS_VERSION}/icons/{n}.svg')}' }},"
              for n in SIMPLE_ICONS]
    block = "const ICONS = {\n" + "\n".join(lines) + "\n};"
    text, n = re.subn(r"const ICONS = \{\n.*?\n\};", lambda m: block, APP.read_text(), count=1, flags=re.S)
    if n != 1:
        raise SystemExit("ICONS block not found in site/app.js")
    APP.write_text(text)
    print(f"wrote {len(lines)} icons to site/app.js")


if __name__ == "__main__":
    main()
