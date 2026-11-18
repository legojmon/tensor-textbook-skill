"""Rebuild the demo from the JSON manuscript and refresh its frozen outputs.

    python tools/refresh_demo.py

Writes examples/demo/demo.html, examples/demo/demo.pdf, tensor/selfcheck/ref/p*.png and docs/preview.png.
Run only after an intentional typesetting change, then run tensor/scripts/selfcheck.py.
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import subprocess
import sys

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "tensor/scripts"
DEMO = ROOT / "examples/demo"
REF = ROOT / "tensor/selfcheck/ref"


def run(script, *args):
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], check=True)


def main():
    run("build.py", ROOT / "tensor/references/example-manuscript.json", "-o", DEMO / "demo.html")
    run("lint.py", DEMO / "demo.html", "--draft")
    run("render.py", DEMO / "demo.html", "-o", DEMO / "demo.pdf", "--strict")
    for old in REF.glob("p*.png"):
        old.unlink()
    REF.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(DEMO / "demo.pdf") as doc:
        for i, page in enumerate(doc, 1):
            page.get_pixmap(dpi=72, colorspace=pymupdf.csGRAY, alpha=False).save(REF / f"p{i:03}.png")
        thumbs = []
        for index in (0, 2, 5, 10):
            pix = doc[min(index, len(doc) - 1)].get_pixmap(dpi=50, alpha=False)
            thumbs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        print(f"데모 {len(doc)}쪽 · 기준 이미지 {len(doc)}장")
    width, height = thumbs[0].size
    sheet = Image.new("RGB", (2 * width + 3, 2 * height + 3), "#dddddd")
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % 2) * (width + 3), (i // 2) * (height + 3)))
    sheet.save(ROOT / "docs/preview.png", optimize=True)


if __name__ == "__main__":
    main()
