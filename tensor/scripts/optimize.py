#!/usr/bin/env python3
"""마지막 단계: 렌더된 PDF 를 원서처럼 가볍게 다시 쓴다 (벡터·글자 그대로, 보기에는 같은 쪽).

    python optimize.py work/book.pdf [-o work/book.pdf] [--check 12]

크롬(Skia)이 만든 PDF 는 글자를 한 자씩 `x 0 Td <글자> Tj` 로 찍는다. 한 쪽에 글자 그리기 명령이 1,000개
가까이 되어 원서 PDF(쪽당 300개 안팎)보다 3배쯤 무겁고, 아이패드·맥의 PDF 엔진에서 쪽이 늦게 뜬다.
이 스크립트는 같은 줄의 글자들을 원서처럼 `[<글자> 간격 <글자> …] TJ` 한 번으로 묶고(글자 위치는 글꼴 폭으로
계산해 그대로 유지), 객체 스트림으로 압축한 뒤 qpdf 로 선형화(빠른 웹 보기)해 첫 쪽이 바로 뜨게 한다.

--check N : 바꾸기 전과 후를 N쪽 골라 그려 보고 픽셀이 같은지 확인한다(기본 12쪽). 다르면 원본을 그대로 둔다.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NUM = r"-?\d*\.?\d+"
BLOCK = re.compile(rb"BT\n(.*?)\nET", re.S)
HEAD = re.compile(rf"^/(\S+) ({NUM}) Tf\n({NUM} {NUM} {NUM} {NUM} {NUM} {NUM}) Tm\n<([0-9A-Fa-f]+)> Tj$".encode())
STEP = re.compile(rf"^({NUM}) 0 Td <([0-9A-Fa-f]+)> Tj$".encode())


def widths(doc, font_xref):
    """Type0(Identity-H) 글꼴의 CID → 폭(1/1000) 표."""
    kind, desc = doc.xref_get_key(font_xref, "DescendantFonts")
    if kind == "null":
        return None
    m = re.search(r"(\d+) 0 R", desc)
    dx = int(m.group(1)) if m else None
    if dx is None:
        return None
    dw = doc.xref_get_key(dx, "DW")
    default = float(dw[1]) if dw[0] != "null" else 1000.0
    kind, w = doc.xref_get_key(dx, "W")
    if kind == "xref":
        w = doc.xref_object(int(w.split()[0]))
    table = {}
    w = (w if kind != "null" else "").strip()
    if w.startswith("[") and w.endswith("]"):
        w = w[1:-1]
    toks = re.findall(r"\[|\]|-?\d*\.?\d+", w)
    i = 0
    while i < len(toks):
        c = int(float(toks[i]))
        if toks[i + 1] == "[":
            j = i + 2
            while toks[j] != "]":
                table[c] = float(toks[j]); c += 1; j += 1
            i = j + 1
        else:
            c2, wv = int(float(toks[i + 1])), float(toks[i + 2])
            for k in range(c, c2 + 1):
                table[k] = wv
            i += 3
    return table, default


def glyph_width(hexs, wt):
    table, default = wt
    return sum(table.get(int(hexs[k:k + 4], 16), default) for k in range(0, len(hexs), 4))


def merge_block(body, fonts):
    lines = body.split(b"\n")
    if len(lines) < 4:
        return None
    m = HEAD.match(b"\n".join(lines[:3]))
    if not m:
        return None
    name, size, tm, first = m.group(1).decode(), float(m.group(2)), m.group(3), m.group(4).decode()
    wt = fonts.get(name)
    if not wt or len(first) % 4 or size == 0:
        return None
    parts, prev = [f"<{first}>"], first
    for ln in lines[3:]:
        s = STEP.match(ln)
        if not s:
            return None
        dx, g = float(s.group(1)), s.group(2).decode()
        if len(g) % 4:
            return None
        n = glyph_width(prev, wt) - dx * 1000.0 / size
        if abs(n) > 0.05:
            parts.append(f"{n:.2f}".rstrip("0").rstrip("."))
        parts.append(f"<{g}>")
        prev = g
    # 같은 숫자 없이 붙는 글자 문자열은 하나로 합친다
    out, buf = [], ""
    for p in parts:
        if p.startswith("<"):
            buf += p[1:-1]
        else:
            if buf:
                out.append(f"<{buf}>"); buf = ""
            out.append(p)
    if buf:
        out.append(f"<{buf}>")
    return (f"/{name} {m.group(2).decode()} Tf\n".encode() + tm + b" Tm\n" + ("[" + " ".join(out) + "] TJ").encode())


def page_fonts(doc, page):
    fonts = {}
    for f in page.get_fonts(full=True):
        xref, name = f[0], f[4]
        if f[2] == "Type0":
            wt = widths(doc, xref)
            if wt:
                fonts[name] = wt
    return fonts


def rewrite(doc):
    before = after = 0
    for page in doc:
        fonts = page_fonts(doc, page)
        if not fonts:
            continue
        for x in page.get_contents():
            data = doc.xref_stream(x)
            before += len(data)
            def sub(m):
                new = merge_block(m.group(1), fonts)
                return b"BT\n" + new + b"\nET" if new is not None else m.group(0)
            new = BLOCK.sub(sub, data)
            after += len(new)
            if new != data:
                doc.update_stream(x, new)
    return before, after


def same(a, b, pages):
    da, db = pymupdf.open(a), pymupdf.open(b)
    worst = 0
    for i in pages:
        pa = da[i].get_pixmap(dpi=110, colorspace=pymupdf.csGRAY).samples
        pb = db[i].get_pixmap(dpi=110, colorspace=pymupdf.csGRAY).samples
        diff = sum(1 for u, v in zip(pa, pb) if abs(u - v) > 48) / len(pa)
        worst = max(worst, diff)
    return worst


def optimize(src, out=None, check=12):
    """src PDF 를 다시 써서 out 에 저장하고 한 줄 보고를 돌려준다. 쪽 모양이 달라지면 원본을 두고 ValueError."""
    src = Path(src)
    out = Path(out or src)
    with tempfile.TemporaryDirectory() as td:
        mid, fin = Path(td) / "mid.pdf", Path(td) / "fin.pdf"
        doc = pymupdf.open(src)
        n = doc.page_count
        before, after = rewrite(doc)
        doc.save(mid, garbage=4, deflate=True, use_objstms=1)
        doc.close()
        linear = bool(shutil.which("qpdf"))
        if linear:
            r = subprocess.run(["qpdf", "--linearize", "--object-streams=generate", str(mid), str(fin)], capture_output=True)
            if r.returncode not in (0, 3):
                fin, linear = mid, False
        else:
            fin = mid
        step = max(1, n // max(1, check))
        worst = same(src, fin, range(0, n, step)) if check else 0.0
        if worst > 0.002:
            raise ValueError(f"바꾼 뒤 쪽 모양이 달라짐(최대 {worst:.2%}) · 원본을 그대로 둔다")
        size0 = src.stat().st_size
        shutil.copyfile(fin, out)
    return (f"{out.name} · 가볍게 다시 씀: 글자 명령 {before // 1024}KB → {after // 1024}KB, "
            f"파일 {size0 / 1e6:.1f} → {out.stat().st_size / 1e6:.1f} MB, 선형화 {'함' if linear else '생략(qpdf 없음)'}, "
            f"쪽 대조 차이 {worst:.3%}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="기본: 원본을 덮어쓴다")
    ap.add_argument("--check", type=int, default=12)
    a = ap.parse_args()
    try:
        print(optimize(a.pdf, a.output, a.check))
    except ValueError as e:
        print(f"[중단] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
