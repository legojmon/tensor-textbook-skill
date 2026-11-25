#!/usr/bin/env python3
"""굿노트용 그림 판(요청할 때만) — 렌더된 내지 PDF 를 쪽 그림 + 보이지 않는 글자 층으로 바꾼다.

    python flatten.py work/book_color.pdf -o work/book_color_goodnotes.pdf [--dpi 180] [--quality 70] [--split]

아이패드의 PDF 엔진은 쪽을 넘기거나 확대할 때마다 내장 글꼴(본문·고딕·수식)과 벡터 그림을 다시 그린다.
쪽 수가 많은 Tensor 책은 굿노트에서 느리게 뜨거나 잠깐 빈 쪽·덜 그려진 쪽으로 보일 수 있다.
이 판은 쪽마다 한 장의 그림(JPEG)으로 바꿔 그런 일이 없고, 원래 글자를 보이지 않는 층으로 겹쳐 두어
굿노트 검색은 그대로 된다. 인쇄에는 원래 PDF 를 쓴다(그림 판은 확대하면 글자 가장자리가 거칠어진다).

--split : Part2 표지 앞에서 둘로 나눠 *_part1.pdf, *_part2.pdf 로도 저장한다(한 권에 Part1·Part2 가 있을 때).
흑백판은 회색조, 컬러판은 컬러로 자동 저장한다.
"""
import argparse
import re
import sys
from pathlib import Path

import pymupdf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def is_color(doc, sample=12):
    """쪽 몇 개를 낮은 해상도로 그려 채도가 있는 픽셀이 있는지 본다."""
    step = max(1, doc.page_count // sample)
    for i in range(0, doc.page_count, step):
        pix = doc[i].get_pixmap(dpi=30)
        s = pix.samples
        for k in range(0, len(s) - 2, 3 * 7):
            r, g, b = s[k], s[k + 1], s[k + 2]
            if max(r, g, b) - min(r, g, b) > 40:
                return True
    return False


def flatten(src, dpi, quality, color, pages=None):
    out = pymupdf.open()
    font = pymupdf.Font("korea")          # 보이지 않는 글자 층용 (검색·복사)
    cs = pymupdf.csRGB if color else pymupdf.csGRAY
    for i in (pages if pages is not None else range(src.page_count)):
        pg = src[i]
        pix = pg.get_pixmap(dpi=dpi, colorspace=cs)
        page = out.new_page(width=pg.rect.width, height=pg.rect.height)
        page.insert_image(page.rect, stream=pix.tobytes("jpg", jpg_quality=quality))
        tw = pymupdf.TextWriter(page.rect)
        for b in pg.get_text("rawdict")["blocks"]:
            for line in b.get("lines", []):
                for sp in line["spans"]:
                    txt = "".join(c["c"] for c in sp["chars"])
                    if txt.strip():
                        try:
                            tw.append(sp["chars"][0]["origin"], txt, font=font, fontsize=sp["size"])
                        except Exception:
                            pass
        tw.write_text(page, render_mode=3)
    toc = src.get_toc()
    if toc and pages is None:
        out.set_toc(toc)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--dpi", type=int, default=180)
    ap.add_argument("--quality", type=int, default=70)
    ap.add_argument("--split", action="store_true", help="Part2 표지 앞에서 나눈 파일도 만든다")
    a = ap.parse_args()
    src = pymupdf.open(a.pdf)
    color = is_color(src)
    out_path = a.output or a.pdf.with_name(a.pdf.stem + "_goodnotes.pdf")
    jobs = [(out_path, None)]
    if a.split:
        cut = next((i for i in range(src.page_count)
                    if re.search(r"P\s*A\s*R\s*T\s*2\s", src[i].get_text()[:200]) and len(src[i].get_text()) < 900), None)
        if cut:
            jobs += [(out_path.with_name(out_path.stem + "_part1.pdf"), range(0, cut)),
                     (out_path.with_name(out_path.stem + "_part2.pdf"), range(cut, src.page_count))]
        else:
            print("※ Part2 표지를 찾지 못해 나누지 않았다")
    for path, rng in jobs:
        doc = flatten(src, a.dpi, a.quality, color, rng)
        doc.save(path, garbage=4, deflate=True)
        print(f"{path} · {doc.page_count}쪽 · {'컬러' if color else '회색조'} {a.dpi}dpi · {path.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
