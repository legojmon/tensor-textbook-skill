#!/usr/bin/env python3
"""TENSOR 앞부분(front matter) 생성기. 한완수 앞부분의 구성과 밀도를 따른다.

    python3 frontmatter.py --authors author/authors.json --book book.json --into work/book.html

book.html 의 <!-- FRONTMATTER --> 자리(없으면 <body> 바로 뒤)에 아래 쪽을 넣는다.
  커리큘럼 → 학기 로드맵 → 독자 수기(동의한 것만) → TENSOR에 대하여 → 서문 → 저자 소개
  → 이 책의 구성 → Part 표지 → Part 전체 차례(자동) → Part 가이드라인 → Method I 시험 개념에 대한 이해
글은 authors.json · book.json 에 있는 것을 쓰고, 없으면 assets/frontmatter.default.json 의 기본 문안을 쓴다.
Method I 의 EX 는 원고의 첫 TOPIC 에서 자동으로 가져온다(원서적 해법 · 시험 개념 박스 · 시험적 해법).
괄호로 시작하는 값("(소속)")은 아직 안 채운 칸으로 보고 넣지 않는다.
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import argparse
import copy
from html import escape
import json
import math
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

from bs4 import BeautifulSoup

START = "<!-- FRONTMATTER -->"
END = "<!-- /FRONTMATTER -->"
HERE = Path(__file__).resolve().parent
DEFAULTS = json.loads((HERE.parent / "assets" / "frontmatter.default.json").read_text(encoding="utf-8"))
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"

TAGS = {
    "[원서 간접 개념]": '<span class="tg ind">원서 간접 개념</span>',
    "[원서 개념]": '<span class="tg ws">원서 개념</span>',
    "[시험 개념]": '<span class="tg">시험 개념</span>',
    "[원서적 해법]": '<span class="tg ws">원서적 해법</span>',
    "[시험적 해법]": '<span class="tg">시험적 해법</span>',
    "[준비]": '<b>[준비]</b>',
}


# ---------------------------------------------------------------- 글 다루기
def filled(v):
    if v is None or v is False:
        return False
    if isinstance(v, str):
        return bool(v.strip()) and not v.strip().startswith("(")
    if isinstance(v, (list, tuple, dict)):
        return len(v) > 0
    return True


def fmt(s):
    """평문 → HTML. 태그 표기와 **굵게** 만 바꾼다."""
    h = escape(str(s or ""))
    for k, v in TAGS.items():
        h = h.replace(escape(k), v)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", h)


def paras(xs, cls=""):
    if isinstance(xs, str):
        xs = [xs]
    c = f' class="{cls}"' if cls else ""
    out = []
    for x in xs or []:
        if isinstance(x, dict) and "quote" in x:
            out.append(f'<p class="fm-quote">{fmt(x["quote"])}</p>')
        elif filled(x):
            out.append(f"<p{c}>{fmt(x)}</p>")
    return "".join(out)


def pairs(xs):
    """[["제목","설명"]] 또는 [{"title","text"}] → [(제목, 설명)]"""
    out = []
    for x in xs or []:
        if isinstance(x, dict):
            t, d = x.get("title"), x.get("text", "")
        elif isinstance(x, (list, tuple)):
            t, d = x[0], (x[1] if len(x) > 1 else "")
        else:
            t, d = x, ""
        if filled(t):
            out.append((t, d))
    return out


def josa(word, a, b):
    """받침 여부로 조사를 고른다. josa('개념', '을', '를') → '을'"""
    w = re.sub(r"[\s)\]』」’'\"]+$", "", word or "")
    if not w:
        return b
    c = w[-1]
    if "가" <= c <= "힣":
        return a if (ord(c) - 0xAC00) % 28 else b
    if c.isdigit():
        return a if c in "013678" else b
    return a if c.lower() in "lmn" else b


def uri(base, p):
    if not filled(p):
        return None
    q = Path(p)
    if not q.is_absolute():
        q = (base / q).resolve()
    return q.as_uri() if q.is_file() else None


# ---------------------------------------------------------------- 쪽 틀
def page(title, body, cls="", run=None, toc=None, guide=None, foot=False, line=False, repeat=False):
    """앞부분 한 묶음. 넘치면 paginate.js 가 다음 쪽으로 이어 붙인다.
    guide=(Part, 제목) 이면 본문 TOPIC 쪽과 같은 머리(띠 + 큰 제목)를 쓴다."""
    if not body:
        return ""
    attrs = ' data-front="1"'
    if run:
        attrs += f' data-run="{escape(run)}"'
    if toc:
        attrs += f' data-toc="{escape(toc)}"'
    if repeat:
        attrs += ' data-repeat-head="1"'
    if line:
        head = '<div class="fm-head guide line"><div class="topline"></div></div>'
    elif guide:
        part, ttl = guide
        head = (f'<div class="fm-head guide"><div class="topic-band">{escape(part)} &nbsp;{escape(ttl)}</div>'
                f'<div class="topic-title"><span class="no">{escape(part)}</span>{escape(ttl)}</div></div>')
    else:
        head = f'<div class="fm-head"><div class="fm-h">{escape(title)}</div></div>'
    nf = "" if foot else " nofoot"
    return (f'<section class="page fm fmflow{nf} {cls}"{attrs}>\n{head}\n'
            f'<div class="fm-body">\n{body}\n</div>\n</section>\n')


def h3(n, t):
    return f'<h3 class="fm-sec"><span class="n">{n}.</span> {fmt(t)}</h3>'


# ---------------------------------------------------------------- 쪽들
def curriculum(A, B, P):
    C = B.get("curriculum") or A.get("curriculum") or DEFAULTS["curriculum"]
    subj = B.get("subject", "")
    rows = []
    for i, s in enumerate(C["stages"]):
        on = " on" if s.get("tag") == P["name"] else ""
        rows.append(
            f'<div class="st{on}"><div class="tag"><b>{escape(s["tag"])}</b></div>'
            f'<div class="tx"><div class="tt">{fmt(s["title"])}</div><p>{fmt(s["text"])}</p></div>'
            f'<div class="who">{fmt(s.get("who", ""))}</div></div>')
        if i < len(C["stages"]) - 1:
            rows.append('<div class="ar">▼</div>')
    body = (f'<div class="fm-subj">{escape(subj)}</div>' if filled(subj) else "") + paras(C.get("lead"), "fm-lead")
    body += f'<div class="fm-stages">{"".join(rows)}</div>'
    series = [s for s in A.get("series", []) if filled(s.get("subject"))]
    if series:
        tr = "".join(
            f'<tr class="{"on" if s.get("subject") == subj else ""}"><td class="sj">{escape(s["subject"])}</td>'
            f'<td>{" · ".join(escape(x) for x in s.get("parts", []) if filled(x))}</td>'
            f'<td class="stt">{escape(s.get("status", ""))}</td></tr>' for s in series)
        body += (f'<div class="fm-sub keep-next">{escape(A.get("brand", "TENSOR"))} 시리즈</div>'
                 f'<table class="fm-tbl series"><tr><th>과목</th><th>구성</th><th>상태</th></tr>{tr}</table>')
    return page(f'{A.get("brand", "TENSOR")} 커리큘럼', body, "fm-curr")


def catmull(pts, n=24):
    """웨이포인트를 지나는 매끄러운 곡선 (Catmull-Rom)"""
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


# 한완수 로드맵과 같은 S자 길 (위에서 아래로, 좌우로 크게 휘어 내려간다)
ROAD = [(x + 25, 40 + (y - 70) * 1.22) for x, y in
        [(380, 70), (275, 70), (205, 105), (190, 165), (225, 215), (310, 232), (385, 245), (425, 295),
         (428, 360), (395, 410), (320, 428), (235, 438), (190, 485), (185, 560), (225, 612), (320, 625), (430, 615)]]
VW, VH, CW, CH = 600, 740, 108, 94
MIDX = 330


def road_svg(points, cards):
    pts = catmull(ROAD)
    seg = [0.0]
    for a, b in zip(pts, pts[1:]):
        seg.append(seg[-1] + math.dist(a, b))
    total = seg[-1]

    def at(f):
        L = f * total
        for i in range(1, len(seg)):
            if seg[i] >= L:
                (x0, y0), (x1, y1) = pts[i - 1], pts[i]
                d = math.dist(pts[i - 1], pts[i]) or 1
                return (x0 + (x1 - x0) * (L - seg[i - 1]) / d, y0 + (y1 - y0) * (L - seg[i - 1]) / d), ((x1 - x0) / d, (y1 - y0) / d)
        return pts[-1], (1, 0)

    n = len(points)
    dots = [at(0.015 + 0.97 * i / max(1, n - 1)) for i in range(n)]
    boxes = []

    def free(x, y, w, h, pad=6):
        if x < 4 or y < 4 or x + w > VW - 4 or y + h > VH - 4:
            return False
        for (px, py) in pts[::2]:
            if x - 13 - pad < px < x + w + 13 + pad and y - 13 - pad < py < y + h + 13 + pad:
                return False
        for (bx, by, bw, bh) in boxes:
            if x < bx + bw + pad and bx < x + w + pad and y < by + bh + pad and by < y + h + pad:
                return False
        return True

    out = []
    card_side = {}
    for c in cards:
        i = c.get("at", 0)
        if not (0 <= i < n):
            continue
        (x, y), (tx, ty) = dots[i]
        nx, ny = -ty, tx
        placed = None
        out_x = -1 if x < MIDX else 1            # 길 바깥쪽(좌우 여백)을 먼저 쓴다
        dirs = [(out_x, 0), (out_x * .7, -.7), (out_x * .7, .7), (nx, ny), (-nx, -ny), (0, -1), (0, 1), (-out_x, 0)]
        for dist in (78, 92, 108, 126):
            for sx, sy in dirs:
                cx, cy = x + sx * dist, y + sy * dist
                bx, by = cx - CW / 2, cy - CH / 2
                if free(bx, by, CW, CH):
                    placed = (bx, by, sx, sy)
                    break
            if placed:
                break
        if not placed:
            continue
        bx, by, sx, sy = placed
        boxes.append((bx, by, CW, CH))
        card_side[i] = (sx, sy)
        # 꼬리: 카드 가장자리에서 점 쪽으로
        cx, cy = bx + CW / 2, by + CH / 2
        ex = min(max(x, bx + 14), bx + CW - 14)
        ey = min(max(y, by + 14), by + CH - 14)
        if abs(sy) >= abs(sx):
            ey = by + CH if y > cy else by
        else:
            ex = bx + CW if x > cx else bx
        vx, vy = x - ex, y - ey
        L = math.hypot(vx, vy) or 1
        tipx, tipy = x - vx / L * 13, y - vy / L * 13
        px, py = -vy / L * 8, vx / L * 8
        out.append(f'<polygon class="tail" points="{ex + px:.1f},{ey + py:.1f} {ex - px:.1f},{ey - py:.1f} {tipx:.1f},{tipy:.1f}"/>')
        out.append(f'<rect class="card" x="{bx:.1f}" y="{by:.1f}" width="{CW}" height="{CH}" rx="7"/>'
                   f'<text x="{cx:.1f}" y="{by + 21:.1f}" class="ct">{escape(str(c.get("top", "")))}</text>'
                   f'<text x="{cx:.1f}" y="{by + 49:.1f}" class="cb">{escape(str(c.get("big", "")))}</text>'
                   f'<line x1="{bx + 14:.1f}" y1="{by + 60:.1f}" x2="{bx + CW - 14:.1f}" y2="{by + 60:.1f}" class="cl"/>'
                   f'<text x="{cx:.1f}" y="{by + 78:.1f}" class="cs">{escape(str(c.get("sub", "")))}</text>')
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    marks = []
    for i, (((x, y), (tx, ty)), p) in enumerate(zip(dots, points)):
        big = p.get("big")
        nx, ny = -ty, tx
        sx, sy = card_side.get(i, (nx, ny))
        lx, ly = x - sx * 24, y - sy * 24          # 카드 반대쪽에 날짜
        if abs(ly - y) < 6:
            ly += 4
        anchor = "middle" if abs(lx - x) < 10 else ("start" if lx > x else "end")
        if i in (0, n - 1):                        # 길 끝의 점은 오른쪽에
            lx, ly, anchor = x + 17, y + 4, "start"
        lab = escape(str(p.get("label", "")))
        sub = escape(str(p.get("sub", "") or ""))
        r = 10 if big else 8
        marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" class="{"dot big" if big else "dot"}"/>')
        t = f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" class="{"pl big" if big else "pl"}">{lab}'
        if sub:
            t += f'<tspan x="{lx:.1f}" dy="13" class="ps">{sub}</tspan>'
        marks.append(t + "</text>")
    return (f'<svg viewBox="0 0 {VW} {VH}" class="fm-road"><path class="rd" d="{d}"/>'
            + "".join(out) + "".join(marks) + "</svg>")


def roadmap(B):
    D = DEFAULTS["roadmap"]
    sem = [s for s in B.get("semester", []) if filled(s.get("label"))]
    points = [{"label": s["label"], "sub": s.get("date") if filled(s.get("date")) else s.get("sub", ""),
               "big": s.get("big")} for s in sem] or D["points"]
    cards = B.get("roadmap_cards") or []
    if not cards:
        n0, n = len(D["points"]), len(points)
        cards = [dict(c, at=round(c["at"] * (n - 1) / (n0 - 1))) for c in D["cards"]]
    year = B.get("year", "")
    return page(f'{year} 로드맵'.strip() if filled(year) else "학기 로드맵", road_svg(points, cards), "fm-roadmap")


def testimonials(B):
    ts = [t for t in B.get("testimonials", []) if t.get("consent") is True and filled(t.get("text"))
          and filled(t.get("name"))]
    body = "".join(f'<div class="fm-testi"><div class="nm">{escape(t["name"])} <small>{escape(t.get("affil", ""))}</small></div>'
                   f'{paras(t["text"] if isinstance(t["text"], list) else [t["text"]])}</div>' for t in ts)
    return page("독자 수기", body, "fm-testis")


def about(A, B):
    items = pairs(A.get("about")) or pairs(DEFAULTS["about"])
    items += [x for x in pairs(B.get("about")) if x[0] not in {i[0] for i in items}]
    brand = A.get("brand", "TENSOR")
    body = f'<div class="fm-sub keep-next">‘{escape(brand)}에 대하여’</div>' + "".join(
        f'<div class="fm-about"><div class="tt"><span class="n">{i + 1}.</span>{fmt(t)}</div>{paras(d if isinstance(d, list) else [d])}</div>'
        for i, (t, d) in enumerate(items))
    return page("소개", body, "fm-aboutp")


def preface(A, B, base, people):
    ps = [p for p in (B.get("preface") or []) if filled(p)] or [p for p in (A.get("preface") or []) if filled(p)]
    if not ps:
        return ""
    names = " · ".join(p["name"] for p in people)
    sign = ""
    for p in people:
        img = uri(base, p.get("signature"))
        if img:
            sign += f'<img class="fm-signimg" src="{img}" alt="">'
    body = f'<div class="fm-prose">{paras(ps)}</div>'
    if names:
        body += f'<div class="fm-sign">{sign}<span>- 저자 {escape(names)} -</span></div>'
    if filled(B.get("thanks") or A.get("thanks")):
        body += f'<p class="fm-thanks">{fmt(B.get("thanks") or A.get("thanks"))}</p>'
    if filled(B.get("preface_note")):
        body += f'<p class="fm-thanks">{fmt(B["preface_note"])}</p>'
    return page("서문", body, "fm-preface")


def authors_page(A, B, base, people):
    cards = []
    for au in people:
        img = uri(base, au.get("photo"))
        av = uri(base, au.get("avatar"))
        if img:      # 사진이 있으면 일러스트는 사진 모서리의 작은 동그라미
            ph = f'<div class="ph"><img class="pic" src="{img}" alt="">' + (f'<img class="av" src="{av}" alt="">' if av else "") + "</div>"
            name_av = ""
        else:        # 사진이 없으면 자리를 비우지 않는다. 일러스트만 이름 옆에 작게
            ph = ""
            name_av = f'<img class="av" src="{av}" alt="">' if av else ""
        bio = "".join(f"<li>{fmt(b)}</li>" for b in au.get("bio", []) if filled(b))
        intro = paras([p for p in au.get("intro", []) if filled(p)])
        scene = (f'<div class="scene"><b>막혔던 장면</b><p>{fmt(au["scene"])}</p></div>'
                 if filled(au.get("scene")) else "")
        msg = f'<p class="msg">{fmt(au["message"])}</p>' if filled(au.get("message")) else ""
        cards.append(f'<div class="fm-author{"" if ph else " nophoto"}">{ph}<div class="info">'
                     f'<div class="nm">{name_av}{escape(au["name"])}<small>{escape(au.get("name_en", ""))}</small></div>'
                     f'<ul>{bio}</ul>{f"<div class=intro>{intro}</div>" if intro else ""}{scene}{msg}</div></div>')
    col = {k: v for k, v in (B.get("colophon") or {}).items() if filled(v)}
    if col:
        cards.append('<table class="fm-tbl colophon">' +
                     "".join(f"<tr><th>{escape(k)}</th><td>{escape(str(v))}</td></tr>" for k, v in col.items()) + "</table>")
    return page("저자 소개", "".join(cards), "fm-authors", repeat=True)


LEGEND = '''
<div class="fm-legend">
  <div class="lg"><div class="demo"><span class="tg ws">원서 개념</span> <span class="tg">시험 개념</span> <span class="tg ind">원서 간접 개념</span></div>
    <div class="tx"><b>개념 태그</b> 실선 = 원서 본문·강의록에 정리된 개념. 검정 = 원서에는 없지만 문제에 반복되는 시험 개념. 점선 = 원서의 예제·부록 등에만 있는 개념.</div></div>
  <div class="lg"><div class="demo"><div class="sol"><span class="lab"><span class="a">원서적</span><span class="b">해법</span></span><div class="box">원서 방식 그대로 푼다</div></div></div>
    <div class="tx"><b>원서적 해법</b> 원서 개념만으로 원서의 방식 그대로 푼 풀이다. 예제마다 먼저 나온다.</div></div>
  <div class="lg"><div class="demo"><div class="sol exam"><span class="lab"><span class="a">시험적</span><span class="b">해법</span></span><div class="box">시험 개념으로 짧게</div></div></div>
    <div class="tx"><b>시험적 해법</b> 시험 개념을 쓴 짧은 풀이다. 맨 앞의 <b>적용 조건</b>을 만족할 때만 쓴다.</div></div>
  <div class="lg"><div class="demo"><div class="concept"><div class="body">시험 개념</div></div><div class="concept book"><div class="body">원서 개념</div></div><div class="concept ind"><div class="body">간접 개념</div></div></div>
    <div class="tx"><b>개념 박스</b> 이중선 = 시험 개념, 실선 = 원서 개념, 점선 = 원서 간접 개념. 시험 개념 박스의 근거는 본문의 원서 개념 논증에 있다.</div></div>
  <div class="lg"><div class="demo"><div class="bubble"><span class="b">이걸 또 처음부터 풀어야 할까?</span></div></div>
    <div class="tx"><b>생각 말풍선</b> 문제를 읽는 순간 가져야 할 의문이다. 시험적 해법은 이 의문에서 출발한다.</div></div>
  <div class="lg"><div class="demo"><div class="core"><span class="lab">CORE</span><div class="box">[조건] ⟹ [바로 할 행동]</div></div></div>
    <div class="tx"><b>CORE</b> TOPIC의 결론 한 줄이다. 복습할 때는 CORE만 이어 읽어도 장 전체가 떠오르게 썼다.</div></div>
  <div class="lg"><div class="demo"><div class="grade"><div class="hd"><span>✎ 답안 · 채점 포인트</span></div></div></div>
    <div class="tx"><b>채점 포인트</b> 서술형 답안에서 점수가 되는 줄과 감점되는 실수를 정리했다.</div></div>
  <div class="lg"><div class="demo"><div class="qh"><div class="no">A·<i>0</i>1</div><div class="meta"><div class="r1"><span class="lv"><i class="on"></i><i class="on"></i><i></i></span><span class="rec">1회<span></span>2회<span></span></span></div><div class="r2"><span class="k">PAGE</span><span class="v">24</span><span class="k">TOPIC</span><span class="v">01</span></div></div></div></div>
    <div class="tx"><b>문제 머리</b> 난이도(칸 수), 풀이 기록, 관련 본문 쪽과 TOPIC이다. 막히면 문제 칸 아래의 <b>힌트</b>를 본다.</div></div>
</div>'''


def structure(B):
    S = B.get("structure") or DEFAULTS["structure"]
    flow = '<div class="fm-flow">' + '<i>→</i>'.join(f"<span>{escape(x)}</span>" for x in S["flow"]) + "</div>"
    parts = "".join(f'<div class="fm-about"><div class="tt"><span class="n">{i + 1}.</span>{fmt(t)}</div><p>{fmt(d)}</p></div>'
                    for i, (t, d) in enumerate(pairs(S["parts"])))
    body = (flow + '<p class="fm-lead">한 장은 위 순서로 짜여 있다. 각 부분의 역할은 다음과 같다.</p>' + parts +
            '<div class="fm-sub keep-next">흑백 표시 읽는 법</div>' + LEGEND)
    return page("이 책의 구성", body, "fm-structure")


def part_info(A, B):
    p = B.get("part") or "Part2"
    if isinstance(p, str):
        name, extra = p, {}
    else:
        name, extra = p.get("name") or "Part2", p
    name = name if name in DEFAULTS["part"] else ("Part1" if "1" in name else "Part2")
    D = dict(DEFAULTS["part"][name])
    D["name"] = name
    D["no"] = re.sub(r"\D", "", name) or "2"
    D["title"] = extra.get("title") or B.get("part_title") or D["title"]
    for k in ("desc", "who", "toc_desc", "goals_note"):
        if filled(extra.get(k)):
            D[k] = extra[k]
    D["check"] = D["check"] + [x for x in extra.get("checklist", []) if filled(x)]
    D["goals"] = D["goals"] + [x for x in extra.get("goals", []) if filled(x)]
    return D


def part_cover(P):
    return (f'<section class="page cover fm-partcover nofoot" data-front="1">'
            f'<div class="brand">TENSOR</div><div class="arch"></div><div class="chap">PART</div>'
            f'<div class="num">{escape(P["no"])}</div><div class="ttl">{escape(P["title"])}</div>'
            f'<div class="note">{fmt(P["desc"]).replace(escape(P["name"]), "<b>" + escape(P["name"]) + "</b>", 1)}</div>'
            f'</section>\n')


def book_toc(B, P):
    subj = B.get("subject", "")
    return (f'<section class="page fm book-toc nofoot" data-front="1" data-toc-host="1">'
            f'<div class="btoc-head"><div class="pc"><small>PART</small><b>{escape(P["no"])}</b></div>'
            f'<div class="hd"><b>{escape(subj)} {escape(P["title"])}</b> <small>: {fmt(P["toc_desc"])}</small></div></div>'
            f'<table class="btoc"></table></section>\n')


def checkbox(P):
    li = "".join(f'<li><span class="n">{CIRCLED[i]}</span>{fmt(x)}</li>' for i, x in enumerate(P["check"]))
    return (f'<div class="fm-check"><div class="hd"><span class="stamp">CHECK</span><b>솔직 자가 진단 표 O/X</b>'
            f'<span class="r">TENSOR {escape(P["name"])} 공부 전 자가 진단</span></div><ol>{li}</ol></div>')


def goals(label, xs):
    li = "".join(f'<div class="g"><span class="n">{CIRCLED[i]}</span>{fmt(x)}</div>' for i, x in enumerate(xs))
    return f'<div class="fm-goals"><div class="lb">{escape(label)} :</div><div>{li}</div></div>'


def guideline(A, P):
    n = P["name"]
    b = h3(1, "어떤 학생이 공부해야 하는가?") + paras([P["who"]]) + checkbox(P)
    b += paras([f"위 항목에 모두 ○라고 답할 수 있어야 {n}를 공부할 준비가 된 것이다. ×가 있다면 해당하는 원서 절로 돌아가 먼저 정리한다."])
    b += h3(2, f"{n}의 목표")
    if n == "Part2":
        b += paras(["TENSOR Part1에서 배운 것을 정리하면 다음과 같다."]) + goals("Part1", P["prev_goals"])
        b += paras(["위 목표를 모두 달성했다면, 이제 [시험 개념]을 심화까지 배울 수 있는 상태다. 따라서 Part2의 목표는 다음과 같다."])
    b += goals(n, P["goals"]) + paras([P["goals_note"]])
    b += h3(3, "메인은 ‘원서 개념’이다.") + paras(DEFAULTS["main_concept"])
    contact = {k: v for k, v in (A.get("contact") or {}).items() if filled(v)}
    if contact:
        rows = "".join(f'<div class="ct"><b>{escape(k)}</b><span>{escape(str(v))}</span></div>' for k, v in contact.items())
        b += h3(4, "소통") + f'<div class="fm-contact">{rows}</div>' + paras([DEFAULTS["contact_note"]], "fm-note")
    return page("", b, "fm-guide", run=f"{n} 가이드라인", toc=f"{n} 가이드라인", guide=(n, "가이드라인"), foot=True)


# ---------------------------------------------------------------- Method I: 원고에서 EX 가져오기
def strip_front(html):
    return re.sub(re.escape(START) + r".*?" + re.escape(END), START, html, flags=re.S)


def examples(html):
    """원고의 TOPIC 에서 [EX, 원서적 해법, 시험 개념 박스, 시험적 해법] 묶음을 찾는다."""
    soup = BeautifulSoup(strip_front(html), "html.parser")
    found = []
    for t in soup.select("article.manuscript > section.topic"):
        if not re.match(r"^\d", t.get("data-no", "")):
            continue
        kids = [k for k in t.children if getattr(k, "name", None)]
        for i, k in enumerate(kids):
            if "ex" not in (k.get("class") or []):
                continue
            grp = {"topic": t.get("data-no"), "title": t.get("data-title", ""), "ex": k}
            for s in kids[i + 1:]:
                c = s.get("class") or []
                if "ex" in c:
                    break
                if "sol" in c and "exam" not in c and "book" not in grp:
                    grp["book"] = s
                elif "concept" in c and "book" not in c and "ind" not in c and "concept" not in grp:
                    grp["concept"] = s
                elif "sol" in c and "exam" in c and "exam" not in grp:
                    grp["exam"] = s
                elif s.name == "div" and "bubble" in c and "bubble" not in grp:
                    grp["bubble"] = s
            if "book" in grp:
                found.append(grp)
    return found


def ex_html(g, no):
    ex = copy.copy(g["ex"])
    for tag in ex.select("[id]"):
        del tag["id"]
    badge = ex.select_one(".badge span")
    if badge:
        badge.string = f"{no:02d}"
    src = ex.select_one(".src")
    note = f"본문 TOPIC {g['topic']}"
    if src:
        src.append(BeautifulSoup(f"<br>[{note}]", "html.parser"))
    return str(ex)


def concept_name(g):
    c = g.get("concept")
    if not c:
        return ""
    t = copy.copy(c.select_one(".ttl"))
    if not t:
        return ""
    for x in t.select(".ico"):
        x.decompose()
    return re.sub(r"\s+", " ", t.get_text(" ")).strip()


def method(P, html):
    if P["name"] != "Part2":
        return ""
    M = DEFAULTS["method"]
    exs = examples(html)
    bar = f'<div class="fm-method"><span class="k">✎ Method I</span><b>{escape(M["title"])}</b></div>'
    b = bar + h3(1, M["why_title"])
    g1 = exs[0] if exs else None
    if g1 and g1.get("concept") and g1.get("exam"):
        name = concept_name(g1)
        nm = f"<b>{escape(name)}</b>"
        b += ex_html(g1, 1) + str(g1["book"]) + str(g1["concept"])
        bridge = fmt(M["why_bridge"]).replace("{concept}을(를)", nm + josa(name, "을", "를")).replace("{concept}", nm)
        b += f"<p>{bridge}</p>" + str(g1["exam"])
        for p in M["why_after"]:
            b += "<p>" + fmt(p).replace("{concept}을(를)", nm + josa(name, "을", "를")).replace("{concept}", nm) + "</p>"
    else:
        b += paras(M["why_fallback"])
    b += h3(2, M["how_title"]) + paras(M["how"])
    b += h3(3, M["main_title"])
    rest = [g for g in exs if g is not g1]
    g2 = next((g for g in rest if g["topic"] != (g1 or {}).get("topic")), rest[0] if rest else None)
    if g2:
        b += ex_html(g2, 1 if not g1 else 2) + str(g2["book"])
        b += paras(M["main_after"])
    else:
        b += paras(M["main_after"][1:])
    T = M["table"]
    feat = "".join(f"<tr>{'' if i else '<th rowspan=' + str(len(T['feature'])) + '>특징</th>'}"
                   f"<td><span class='n'>{CIRCLED[i]}</span>{fmt(a)}</td><td><span class='n'>{CIRCLED[i]}</span>{fmt(c)}</td></tr>"
                   for i, (a, c) in enumerate(T["feature"]))
    b += paras(["정리하면 다음과 같다."])
    b += (f'<table class="fm-cmp"><tr><th></th><th>{fmt(T["head"][0])}</th><th>{fmt(T["head"][1])}</th></tr>{feat}'
          f'<tr><th>목표</th><td colspan="2">{fmt(T["goal"])}</td></tr></table>')
    b += paras(M["closing"])
    return page("", b, "fm-methodp", run=M["title"], toc=M["title"], foot=True, line=True)


# ---------------------------------------------------------------- 조립
def render(A, B, base, html=""):
    people = [p for p in A.get("authors", []) if filled(p.get("name"))]
    P = part_info(A, B)
    pages = [curriculum(A, B, P), roadmap(B), testimonials(B), about(A, B), preface(A, B, base, people),
             authors_page(A, B, base, people), structure(B), part_cover(P), book_toc(B, P),
             guideline(A, P), method(P, html)]
    return "".join(p for p in pages if p)


def insert(source, pages):
    block = START + "\n" + pages + END
    if START in source:
        if source.count(START) != 1 or source.count(END) > 1:
            raise ValueError("앞부분 삽입 표식이 중복되었습니다.")
        start = source.index(START)
        end = source.index(END, start) + len(END) if END in source else start + len(START)
        return source[:start] + block + source[end:]
    body = re.search(r"<body\b[^>]*>", source, re.IGNORECASE)
    if not body:
        raise ValueError("원고에서 body 태그를 찾을 수 없습니다.")
    return source[:body.end()] + "\n" + block + source[body.end():]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--authors", required=True, type=Path)
    parser.add_argument("--book", required=True, type=Path)
    parser.add_argument("--into", required=True, type=Path)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
    source = args.into.read_text(encoding="utf-8")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import stamp
    ok, why = stamp.verify(source)
    if not ok:
        raise SystemExit(f"[앞부분 거부] {args.into.name}: {why}")
    A, B = load(args.authors), load(args.book)
    pages = render(A, B, args.authors.resolve().parent, source)
    result = stamp.seal(insert(source, pages))
    with NamedTemporaryFile(mode="w", dir=args.into.parent, encoding="utf-8", newline="\n", delete=False) as tmp:
        tmp.write(result)
    try:
        os.replace(tmp.name, args.into)
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    made = re.findall(r'class="fm-h">([^<]+)<|data-run="([^"]+)"|class="page cover fm-partcover', pages)
    names = [a or b or "Part 표지" for a, b in made]
    print("앞부분:", " → ".join(dict.fromkeys(names)), "→ Part 전체 차례(자동)")
    if not examples(source):
        print("※ Method I 에 쓸 EX(원서적 해법이 있는 예제)를 원고에서 찾지 못해 설명 글만 넣었다.")
    empty = [p["name"] for p in A.get("authors", []) if filled(p.get("name")) and not filled(p.get("photo"))]
    if empty:
        print("※ 사진 없이 넣은 저자(자리 비우지 않음):", ", ".join(empty))


if __name__ == "__main__":
    main()
