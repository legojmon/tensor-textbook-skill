"""원고 조립 보조 — 배열 매크로와 컬러판 그림 변환. build.py 가 불러 쓴다.

배열 한 줄은 원고 문자열 안에 매크로로 쓴다(그림 대신):
  [[arr 5 2 _ 9 | idx=0 | hl=1 | dark=3 | dim=0-1 | bar=2 | mark=0:L,3:R | lab=pass 1 | cap=교환 1회]]
  _ 는 빈칸, ~ 는 공백. idx=첫 칸 번호(생략하면 번호 줄 없음)
  hl=굵은 테두리 · dark=강조색 칸 · dim=회색(확정 영역) · bar=오른쪽 굵은 칸막이 · mark=칸 아래 표시
코드 블록은 {"type": "code"} 블록, 본문 속 코드 조각은 <code class="c">…</code> 로 쓴다. CSS 는 tensor.css 에 있다.
"""
import re
from pathlib import Path

ARR = re.compile(r"\[\[arr (.*?)\]\]", re.S)


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
    rows = ["<tr>" + "".join(cells) + "</tr>"]
    if idx is not None:
        rows.append('<tr class="ix">' + "".join(f"<td>{int(idx) + i}</td>" for i in range(len(vals))) + "</tr>")
    if marks:
        rows.append('<tr class="mk">' + "".join(f"<td>{marks.get(i, '')}</td>" for i in range(len(vals))) + "</tr>")
    s = '<div class="arrw">'
    if opt.get("lab"):
        s += f'<span class="al">{opt["lab"]}</span>'
    s += '<table class="arr">' + "".join(rows) + "</table>"
    if opt.get("cap"):
        s += f'<span class="ac">{opt["cap"]}</span>'
    return s + "</div>"


def expand_arrays(html):
    return ARR.sub(arr, html)


def colorize_figs(fig_dir, out_dir, accent):
    """흑백 그림(fig/*.svg)의 굵은 선과 검정 채움을 강조색으로 바꾼 figc/ 를 만든다 (dsfig.py 그림 기준)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def el(m):
        e = m.group(0)
        if re.search(r'stroke-width="2\.[2-9]"', e):
            e = e.replace('stroke="#111"', f'stroke="{accent}"')
        if re.search(r'<(circle|rect)[^>]*fill="#111"', e):
            e = e.replace('fill="#111"', f'fill="{accent}"').replace('stroke="#111"', f'stroke="{accent}"')
        return e
    for f in sorted(Path(fig_dir).glob("*.svg")):
        (out_dir / f.name).write_text(re.sub(r'<(circle|rect|line|path)[^>]*/>', el, f.read_text(encoding="utf-8")), encoding="utf-8")
    for f in Path(fig_dir).glob("*.png"):
        (out_dir / f.name).write_bytes(f.read_bytes())
