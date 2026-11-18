#!/usr/bin/env python3
"""원고 전처리 — 배열 매크로, 코드 블록, 워밍업 "준비" 칸 CSS, 흑백/컬러 두 벌 출력.

    python3 prep.py work/src.html work/book.html                 # 흑백(인쇄용)
    python3 prep.py work/src.html work/book_color.html --color   # 컬러(화면용): theme-mono 제거, fig/ → figc/

원고에서 쓰는 것
  [[arr 5 2 _ 9 | idx=0 | hl=1 | dark=3 | dim=0-1 | bar=2 | mark=0:L,3:R | lab=pass 1 | cap=교환 1회]]
      배열 한 줄. _ 는 빈칸, ~ 는 공백. idx=첫 칸 번호(생략하면 번호 줄 없음)
      hl=굵은 테두리 · dark=강조색 칸 · dim=회색(확정 영역) · bar=오른쪽 굵은 칸막이 · mark=칸 아래 표시
  <pre class="code">…</pre>   코드 블록. 안의 < > & 는 그대로 쓴다(자동 이스케이프). [[b]]…[[/b]] = 강조 줄
  <code class="c">…</code>    본문 속 코드 조각
  <div class="pre"><b>준비</b>…</div>   워밍업 문제의 정의·규칙 칸 (.qitem .t 맨 앞)
  <table class="trace">       단계별 추적 표(작은 글자)

--color 일 때 흑백 그림 fig/*.svg 를 강조색으로 바꾼 figc/*.svg 를 출력 파일 옆에 만든다.
굵은 선(stroke-width 2.2~2.9)과 검정 채움 원·사각형만 강조색으로 바뀐다(dsfig.py 그림 기준).
"""
import argparse
import html as H
import re
import sys
from pathlib import Path

CSS = """<style>
.arrw{margin:1.6mm 0;display:flex;align-items:center;gap:2.5mm;justify-content:center}
.arrw .al{font-family:var(--sans);font-size:7.4pt;font-weight:700;min-width:11mm;text-align:right;color:#333}
table.arr{border-collapse:collapse;font-family:var(--sans);font-size:8.4pt;margin:0;width:auto}
table.arr td{border:1px solid #111;min-width:6.2mm;height:5.8mm;text-align:center;padding:0 .6mm;line-height:1.1}
table.arr td.hl{outline:2px solid #111;outline-offset:-2px;font-weight:800}
table.arr td.dark{background:var(--p);color:#fff;font-weight:700}
table.arr td.dim{background:#dedede}
table.arr td.bar{border-right:3px solid #111}
table.arr tr.ix td{border:none;font-size:6.2pt;color:#777;height:3.2mm}
table.arr tr.mk td{border:none;font-size:6.6pt;font-weight:800;height:3.4mm}
.arrw .ac{font-family:var(--sans);font-size:7pt;color:#555}
pre.code{font-family:"DejaVu Sans Mono",monospace;font-size:7.3pt;line-height:1.42;background:#f3f3f3;border-left:2.2px solid var(--p);
 padding:1.8mm 3mm;margin:2mm 0;white-space:pre;overflow:hidden;border-radius:0 1.5mm 1.5mm 0}
pre.code b{font-family:"DejaVu Sans Mono",monospace;background:#d0d0d0}
.qitem pre.code{font-size:6.9pt;margin:1.2mm 0}
code.c{font-family:"DejaVu Sans Mono",monospace;font-size:.9em;background:#eee;padding:0 .6mm;border-radius:.6mm}
.figrow{display:flex;gap:4mm;justify-content:center;align-items:flex-end;flex-wrap:wrap;margin:2mm 0}
.figrow .fig{text-align:center}
table.arr td.n{border:none}
.concept td:first-child,.vs td:first-child{white-space:nowrap}
div.pre{font-family:var(--sans);font-size:7.6pt;line-height:1.5;border:1px dashed var(--pm);border-radius:1.5mm;padding:1.4mm 2.4mm;margin:0 0 2mm;background:var(--pl)}
div.pre b{color:var(--p);margin-right:1.5mm}
.labnote{font-size:8.6pt}
table.trace{font-size:7.8pt}
table.trace td,table.trace th{padding:.6mm 1.4mm}
</style>"""


def rng(s):
    out = set()
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def arr(m):
    parts = [p.strip() for p in m.group(1).split("|")]
    vals = parts[0].split()
    opt = {}
    for p in parts[1:]:
        k, _, v = p.partition("=")
        opt[k.strip()] = v.strip()
    idx = opt.get("idx")
    hl, dark, dim, bar = (rng(opt.get(k, "")) for k in ("hl", "dark", "dim", "bar"))
    marks = {}
    for t in opt.get("mark", "").split(","):
        if ":" in t:
            i, s = t.split(":", 1)
            marks[int(i)] = s
    cells = []
    for i, v in enumerate(vals):
        c = [k for k, S in (("hl", hl), ("dark", dark), ("dim", dim), ("bar", bar)) if i in S]
        txt = "" if v == "_" else v.replace("~", " ")
        cells.append(f'<td class="{" ".join(c)}">{txt}</td>')
    rows = ['<tr>' + "".join(cells) + '</tr>']
    if idx is not None:
        rows.append('<tr class="ix">' + "".join(f"<td>{int(idx)+i}</td>" for i in range(len(vals))) + "</tr>")
    if marks:
        rows.append('<tr class="mk">' + "".join(f"<td>{marks.get(i, '')}</td>" for i in range(len(vals))) + "</tr>")
    lab = opt.get("lab", "")
    cap = opt.get("cap", "")
    s = '<div class="arrw">'
    if lab:
        s += f'<span class="al">{lab}</span>'
    s += '<table class="arr">' + "".join(rows) + "</table>"
    if cap:
        s += f'<span class="ac">{cap}</span>'
    return s + "</div>"


def pre(m):
    body = m.group(2)
    body = body.strip("\n")
    esc = H.escape(H.unescape(body), quote=False)
    esc = esc.replace("[[b]]", "<b>").replace("[[/b]]", "</b>")
    return f'<pre class="code"{m.group(1)}>{esc}</pre>'


def colorize_figs(fig_dir, out_dir, accent):
    out_dir.mkdir(parents=True, exist_ok=True)
    def el(m):
        e = m.group(0)
        if re.search(r'stroke-width="2\.[2-9]"', e):
            e = e.replace('stroke="#111"', f'stroke="{accent}"')
        if re.search(r'<(circle|rect)[^>]*fill="#111"', e):
            e = e.replace('fill="#111"', f'fill="{accent}"').replace('stroke="#111"', f'stroke="{accent}"')
        return e
    for f in sorted(fig_dir.glob("*.svg")):
        s = re.sub(r'<(circle|rect|line|path)[^>]*/>', el, f.read_text(encoding="utf-8"))
        (out_dir / f.name).write_text(s, encoding="utf-8")
    for f in fig_dir.glob("*.png"):
        (out_dir / f.name).write_bytes(f.read_bytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--color", action="store_true", help="컬러판: theme-mono 제거, fig/ → figc/")
    ap.add_argument("--accent", default="#6B3FD4", help="컬러판 그림 강조색")
    a = ap.parse_args()
    t = Path(a.src).read_text(encoding="utf-8")
    if a.color:
        t = re.sub(r'<link rel="stylesheet" href="[^"]*theme-mono\.css">', "", t)
        t = t.replace('src="fig/', 'src="figc/')
        fig = Path(a.out).resolve().parent / "fig"
        if fig.is_dir():
            colorize_figs(fig, fig.parent / "figc", a.accent)
    t = re.sub(r'<pre class="code"([^>]*)>(.*?)</pre>', pre, t, flags=re.S)
    t = re.sub(r"\[\[arr (.*?)\]\]", arr, t, flags=re.S)
    t = t.replace("</head>", CSS + "\n</head>", 1)
    Path(a.out).write_text(t, encoding="utf-8")
    print(a.out)


if __name__ == "__main__":
    main()
