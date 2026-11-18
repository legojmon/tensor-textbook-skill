#!/usr/bin/env python3
"""그림 도구 — 원본 자르기, 흑백 변환, 원본↔다시 그린 그림 대조.

  # PDF 쪽에서 영역 자르기 (좌표는 PDF pt; 쪽 이미지에서 픽셀로 잰 값이면 --px 와 --dpi 를 준다)
  python3 figtools.py crop 강의록.pdf 12 --box 330 80 700 300 -o fig/l02_orig.png
  python3 figtools.py crop 원서.pdf 747 --box 100 300 400 520 --px --dpi 110 -o fig/a01_orig.png

  # 대조 시트: 원본 | 다시 그린 그림 (SVG/PNG) 을 나란히 → 직접 열어 소자·라벨·방향을 하나씩 비교
  python3 figtools.py compare work/figures/fig_P14.7-6_p747.png fig/a01.svg -o work/compare/a01.png

  # 원본을 그대로 쓰기로 한 경우(개인 인쇄용): 흑백·대비 보정
  python3 figtools.py mono in.png -o fig/a01.png
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import argparse
from pathlib import Path


def crop(a):
    import pymupdf
    d = pymupdf.open(a.pdf)
    pg = d[a.page - 1]
    x0, y0, x1, y1 = a.box
    if a.px:
        k = 72 / a.dpi
        x0, y0, x1, y1 = x0 * k, y0 * k, x1 * k, y1 * k
    pix = pg.get_pixmap(dpi=a.out_dpi, clip=pymupdf.Rect(x0, y0, x1, y1), colorspace=pymupdf.csGRAY)
    Path(a.o).parent.mkdir(parents=True, exist_ok=True)
    pix.save(a.o)
    print(a.o)


def read_figure(path, width=900):
    from PIL import Image
    import pymupdf
    if Path(path).suffix.lower() != ".svg":
        with Image.open(path) as image:
            return image.convert("RGB")
    with pymupdf.open(path) as document:
        page = document[0]
        scale = width / page.rect.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csRGB, alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def compare(a):
    from PIL import Image, ImageDraw, ImageOps
    ims = [ImageOps.contain(read_figure(x), (900, 650)) for x in (a.original, a.redrawn)]
    w = sum(i.width for i in ims) + 60
    h = max(i.height for i in ims) + 50
    sh = Image.new("RGB", (w, h), "white")
    dr = ImageDraw.Draw(sh)
    x = 20
    for lab, im in zip(("원본", "다시 그림"), ims):
        sh.paste(im, (x, 40))
        dr.text((x, 10), lab, fill="black")
        x += im.width + 20
    Path(a.o).parent.mkdir(parents=True, exist_ok=True)
    sh.save(a.o)
    print(a.o, "← 이 이미지를 열어 소자 값·라벨·방향·연결을 하나씩 대조하세요")


def mono(a):
    from PIL import Image, ImageOps, ImageEnhance
    im = ImageOps.grayscale(Image.open(a.inp))
    im = ImageEnhance.Contrast(im).enhance(1.4)
    im.save(a.o)
    print(a.o)


ap = argparse.ArgumentParser()
sp = ap.add_subparsers(dest="cmd", required=True)
c = sp.add_parser("crop"); c.add_argument("pdf"); c.add_argument("page", type=int)
c.add_argument("--box", nargs=4, type=float, required=True); c.add_argument("--px", action="store_true")
c.add_argument("--dpi", type=int, default=110); c.add_argument("--out-dpi", type=int, default=200); c.add_argument("-o", required=True)
c.set_defaults(fn=crop)
m = sp.add_parser("compare"); m.add_argument("original"); m.add_argument("redrawn"); m.add_argument("-o", required=True)
m.set_defaults(fn=compare)
g = sp.add_parser("mono"); g.add_argument("inp"); g.add_argument("-o", required=True)
g.set_defaults(fn=mono)
a = ap.parse_args()
a.fn(a)
