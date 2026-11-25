#!/usr/bin/env python3
"""태블릿판 — 아이패드·갤럭시(굿노트, 삼성 노트, 기본 PDF 뷰어)에서 렌더링 오류가 없게 만든 화면용 PDF.

    python tablet.py work/book_color.pdf [-o work/book_tablet.pdf] [--split] [--dpi 220] [--quality 82]

인쇄용 PDF(벡터, 흑백)와 다르다. 컬러판의 각 쪽을 그대로 한 장의 그림으로 굽고, 그 위에 원래 글자를
보이지 않는 층으로 겹친다. 내용·쪽 배치·디자인·글꼴은 컬러판과 똑같이 보이고, 기기의 PDF 엔진은 쪽마다
그림 한 장만 그리면 되므로 글꼴·벡터 도형·투명 효과 때문에 생기는 빈 쪽, 부분부분 흰 상자, 늦게 채워지는
표·그림이 생기지 않는다. 검색·글자 복사는 보이지 않는 글자 층으로 그대로 된다. 장·TOPIC 책갈피(목차)를 붙인다.

--split : 한 권에 Part1·Part2 가 있으면 Part2 표지 앞에서 나눈 파일(_Part1, _Part2)도 만든다(태블릿에서 더 가볍다).
"""
import argparse
import re
import sys
from pathlib import Path

import pymupdf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def outline(src):
    """쪽 글자로 Part·장·TOPIC 책갈피를 만든다: [(level, title, page_index)]."""
    marks = []
    for i, pg in enumerate(src):
        t = pg.get_text()
        head = [ln.strip() for ln in t.split("\n")[:6] if ln.strip()]
        m = re.match(r"T\s*E\s*N\s*S\s*O\s*R\s*\nP\s*\nA\s*\nR\s*\nT\s*\n(\d)\s*\n([^\n]+)", t)
        if m:
            marks.append((1, f"Part{m.group(1)} {m.group(2).strip()}", i))
            continue
        m = re.match(r"T\s*E\s*N\s*S\s*O\s*R\s*\nC\s*\nH\s*\nA\s*\nP\s*\nT\s*\nE\s*\nR\s*\n(\d+)\s*\n([^\n]+)", t)
        if m:
            marks.append((2, f"{m.group(1)}. {m.group(2).strip()}", i))
            continue
        for ln in head[:3]:
            mt = re.match(r"^TOPIC (\d{2}) (?![.·])(.+)$", ln)
            if mt:
                marks.append((3, f"TOPIC {mt.group(1)} {mt.group(2)}", i))
                break
        if head and head[0] == "개념 박스 인덱스":
            pass
    last_topic = max((p for lv, _, p in marks if lv == 3), default=-1)
    later = [i for i, pg in enumerate(src) if i > last_topic and "개념 박스 인덱스" in pg.get_text()
             and ("개념 박스와 저자의 특강" in pg.get_text()[:200])]
    if later:
        marks.append((1, "개념 박스 인덱스", later[0]))
    # 장 표지 없이 TOPIC 이 먼저 나오면 단계를 맞춘다
    out, level = [], 0
    for lv, title, page in marks:
        lv = min(lv, level + 1) if out else 1
        out.append((lv, title, page))
        level = lv
    return out


def bake(src, dpi, quality, pages, font):
    out = pymupdf.open()
    for i in pages:
        pg = src[i]
        pix = pg.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
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
        tw.write_text(page, render_mode=3)          # 보이지 않는 글자(검색·복사용)
    return out


def save(doc, path, marks, first, title):
    toc = [[lv, t, p - first + 1] for lv, t, p in marks if first <= p < first + doc.page_count]
    fixed, prev = [], 0
    for lv, t, p in toc:                              # PDF 책갈피는 단계를 한 번에 하나씩만 내려갈 수 있다
        lv = 1 if not fixed else min(lv, prev + 1)
        fixed.append([lv, t, p]); prev = lv
    if fixed:
        doc.set_toc(fixed)
    doc.set_metadata({"title": title, "producer": "TENSOR tablet.py", "creator": "TENSOR"})
    doc.save(path, garbage=4, deflate=True)
    print(f"{path} · {doc.page_count}쪽 · 책갈피 {len(fixed)}개 · {path.stat().st_size / 1e6:.1f} MB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path, help="컬러판 PDF (render.py 결과)")
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--dpi", type=int, default=220)
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--split", action="store_true")
    a = ap.parse_args()
    src = pymupdf.open(a.pdf)
    font = pymupdf.Font("korea")
    marks = outline(src)
    out = a.output or a.pdf.with_name(a.pdf.stem.replace("_color", "") + "_tablet.pdf")
    title = src.metadata.get("title") or out.stem
    save(bake(src, a.dpi, a.quality, range(src.page_count), font), out, marks, 0, title)
    if a.split:
        cut = next((p for lv, t, p in marks if lv == 1 and t.startswith("Part2")), None)
        if cut:
            for name, rng in (("_Part1", range(0, cut)), ("_Part2", range(cut, src.page_count))):
                save(bake(src, a.dpi, a.quality, rng, font), out.with_name(out.stem + name + ".pdf"), marks, rng.start, title + name)
        else:
            print("※ Part2 표지가 없어 나누지 않았다")


if __name__ == "__main__":
    main()
