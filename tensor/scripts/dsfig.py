"""자료구조 그림 도구 (흑백 인쇄용 SVG).

tree(spec, ...)   이진 트리: (label, L, R) / 일반 트리: (label, [children])
graph(V, E, ...)  정점 좌표 dict, 간선 [(u, v, w)]
라벨이 겹치면 'key@id' 로 구분한다 (화면에는 key 만 보임).
"""
from pathlib import Path
from xml.sax.saxutils import escape

INK = "#111"
GRAY = "#888"
LIGHT = "#d9d9d9"
FONT = "Noto Sans CJK KR, Pretendard, sans-serif"
R = 11


def _show(lbl):
    return str(lbl).split("@")[0]


def _is_general(node):
    return isinstance(node, tuple) and len(node) == 2 and isinstance(node[1], list)


def _layout(spec):
    pos, edges, order = {}, [], []
    if spec is None:
        return pos, edges
    if _is_general(spec):
        leaf = [0]

        def rec(n, d):
            lbl, ch = n
            if not ch:
                x = leaf[0]
                leaf[0] += 1
            else:
                xs = []
                for c in ch:
                    rec(c, d + 1)
                    edges.append((lbl, c[0], None))
                    xs.append(pos[c[0]][0])
                x = (xs[0] + xs[-1]) / 2
            pos[lbl] = (x, d)
        rec(spec, 0)
        return pos, edges
    cnt = [0]

    def rec(n, d):
        if n is None:
            return
        lbl, L, Rr = n
        rec(L, d + 1)
        pos[lbl] = (cnt[0], d)
        cnt[0] += 1
        rec(Rr, d + 1)
        if L is not None:
            edges.append((lbl, L[0], "L"))
        if Rr is not None:
            edges.append((lbl, Rr[0], "R"))
    rec(spec, 0)
    return pos, edges


def _svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'font-family="{FONT}">' + "".join(body) + "</svg>")


def node_svg(x, y, lbl, kind="c", hl=False, dark=False, dashed=False, r=R, fs=11):
    sw = 2.4 if hl else 1.1
    fill = INK if dark else ("#fff" if not dashed else "#fff")
    tc = "#fff" if dark else INK
    da = ' stroke-dasharray="3 2"' if dashed else ""
    if kind == "s":
        s = f'<rect x="{x-r*.85:.1f}" y="{y-r*.85:.1f}" width="{r*1.7:.1f}" height="{r*1.7:.1f}" fill="{LIGHT if not dark else INK}" stroke="{INK}" stroke-width="{sw}"{da}/>'
    else:
        s = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="{sw}"{da}/>'
    t = escape(_show(lbl))
    f = fs if len(t) <= 2 else fs - 2
    s += f'<text x="{x:.1f}" y="{y+f*0.36:.1f}" font-size="{f}" text-anchor="middle" fill="{tc}" font-weight="{700 if hl or dark else 500}">{t}</text>'
    return s


def tree(spec, out, dx=26, dy=38, hl=(), dark=(), ann=None, hle=(), dashe=(), sq=(), ghost=(), note=None,
         annpos="ur", extra=None, pad=14, edge_lbl=None):
    """hl: 굵은 테두리, dark: 검정 채움, ann: {label: '작은 글씨'}, hle: 굵은 간선 {(p,c)},
    sq: 사각형(외부 노드), ghost: 점선 노드, note: 아래 캡션 문자열"""
    ann = ann or {}
    pos, edges = _layout(spec)
    xs = [p[0] for p in pos.values()] or [0]
    ys = [p[1] for p in pos.values()] or [0]
    W = (max(xs) - min(xs)) * dx + 2 * pad + 2 * R + (18 if ann else 0)
    H = (max(ys)) * dy + 2 * pad + 2 * R + (16 if note else 0)
    ox = pad + R - min(xs) * dx + (6 if ann else 0)
    oy = pad + R

    def P(l):
        x, y = pos[l]
        return ox + x * dx, oy + y * dy
    body = []
    for a, b, _ in edges:
        (x1, y1), (x2, y2) = P(a), P(b)
        thick = (a, b) in hle
        da = ' stroke-dasharray="4 3"' if (a, b) in dashe else ""
        body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{INK}" stroke-width="{2.6 if thick else 1.1}"{da}/>')
        if edge_lbl and (a, b) in edge_lbl:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            off = -9 if x2 < x1 else 9
            body.append(f'<text x="{mx+off:.1f}" y="{my:.1f}" font-size="9" text-anchor="middle" fill="{INK}">{escape(edge_lbl[(a,b)])}</text>')
    for l in pos:
        x, y = P(l)
        body.append(node_svg(x, y, l, "s" if l in sq else "c", l in hl, l in dark, l in ghost))
        if l in ann:
            if annpos == "ur":
                body.append(f'<text x="{x+R+1:.1f}" y="{y-R+3:.1f}" font-size="8.5" fill="{GRAY}" font-weight="700">{escape(str(ann[l]))}</text>')
            else:
                body.append(f'<text x="{x-R-1:.1f}" y="{y-R+3:.1f}" font-size="8.5" fill="{GRAY}" text-anchor="end" font-weight="700">{escape(str(ann[l]))}</text>')
    if extra:
        body.append(extra(P))
    if note:
        body.append(f'<text x="{W/2:.1f}" y="{H-4:.1f}" font-size="9.5" text-anchor="middle" fill="{INK}">{escape(note)}</text>')
    Path(out).write_text(_svg(W, H, body), encoding="utf-8")
    return out


def graph(V, E, out, scale=46, directed=False, hl=(), dashe=(), hlv=(), darkv=(), ann=None, pad=16,
          wpos=None, note=None, r=R, curved=()):
    """V: {name: (x, y)}  (y 아래로 증가), E: [(u, v, w)] w 는 None 가능.
    hl: 굵은 간선 {(u,v)}, dashe: 점선 간선, hlv: 굵은 정점, darkv: 검정 정점, ann: {v: '작은 글씨'}"""
    ann = ann or {}
    wpos = wpos or {}
    xs = [p[0] for p in V.values()]
    ys = [p[1] for p in V.values()]
    W = (max(xs) - min(xs)) * scale + 2 * pad + 2 * r + 20
    H = (max(ys) - min(ys)) * scale + 2 * pad + 2 * r + 10 + (16 if note else 0)
    ox = pad + r + 10 - min(xs) * scale
    oy = pad + r + 5 - min(ys) * scale

    def P(v):
        return ox + V[v][0] * scale, oy + V[v][1] * scale
    body = []
    if directed:
        body.append(f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>')
    def key(u, v):
        return (u, v) if directed else tuple(sorted((u, v)))
    hlk = {key(*e) for e in hl}
    dak = {key(*e) for e in dashe}
    for e in E:
        u, v, w = e
        (x1, y1), (x2, y2) = P(u), P(v)
        k = key(u, v)
        thick = k in hlk
        da = ' stroke-dasharray="5 3"' if k in dak else ""
        import math
        L = math.hypot(x2 - x1, y2 - y1) or 1
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        sx, sy = x1 + ux * r, y1 + uy * r
        ex, ey = x2 - ux * (r + (1.5 if directed else 0)), y2 - uy * (r + (1.5 if directed else 0))
        mk = ' marker-end="url(#ar)"' if directed else ""
        if (u, v) in curved:
            cx, cy = (sx + ex) / 2 - uy * 14, (sy + ey) / 2 + ux * 14
            body.append(f'<path d="M{sx:.1f},{sy:.1f} Q{cx:.1f},{cy:.1f} {ex:.1f},{ey:.1f}" fill="none" stroke="{INK}" stroke-width="{2.8 if thick else 1.1}"{da}{mk}/>')
            mx, my = (sx + 2 * cx + ex) / 4, (sy + 2 * cy + ey) / 4
        else:
            body.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{INK}" stroke-width="{2.8 if thick else 1.1}"{da}{mk}/>')
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if w is not None:
            off = wpos.get((u, v), wpos.get((v, u), (0, 0)))
            nx, ny = -uy * 7, ux * 7
            tx, ty = mx + nx + off[0], my + ny + off[1]
            body.append(f'<rect x="{tx-7:.1f}" y="{ty-7:.1f}" width="14" height="12" fill="#fff"/>')
            body.append(f'<text x="{tx:.1f}" y="{ty+2.5:.1f}" font-size="9.5" text-anchor="middle" fill="{INK}" font-weight="{700 if thick else 400}">{escape(str(w))}</text>')
    for v in V:
        x, y = P(v)
        body.append(node_svg(x, y, v, "c", v in hlv, v in darkv, r=r))
        if v in ann:
            a = ann[v]
            if isinstance(a, tuple):
                txt, (axo, ayo) = a
            else:
                txt, (axo, ayo) = a, (r + 2, -r + 2)
            body.append(f'<text x="{x+axo:.1f}" y="{y+ayo:.1f}" font-size="8.5" fill="{GRAY}" font-weight="700">{escape(str(txt))}</text>')
    if note:
        body.append(f'<text x="{W/2:.1f}" y="{H-4:.1f}" font-size="9.5" text-anchor="middle" fill="{INK}">{escape(note)}</text>')
    Path(out).write_text(_svg(W, H, body), encoding="utf-8")
    return out


def row(labels, out, cell=22, idx=None, hl=(), dark=(), dim=(), arrows=None, note=None, h=22):
    """배열 한 줄 SVG (그림 안에서 쓸 때). 본문 배열은 HTML 매크로 [[arr]] 를 쓴다."""
    n = len(labels)
    W = n * cell + 4
    H = h + 4 + (12 if idx is not None else 0) + (14 if note else 0)
    body = []
    for i, v in enumerate(labels):
        x = 2 + i * cell
        fill = INK if i in dark else (LIGHT if i in dim else "#fff")
        body.append(f'<rect x="{x}" y="2" width="{cell}" height="{h}" fill="{fill}" stroke="{INK}" stroke-width="{2.2 if i in hl else 1}"/>')
        body.append(f'<text x="{x+cell/2}" y="{2+h/2+4}" font-size="10" text-anchor="middle" fill="{"#fff" if i in dark else INK}">{escape(str(v))}</text>')
        if idx is not None:
            body.append(f'<text x="{x+cell/2}" y="{h+14}" font-size="8" text-anchor="middle" fill="{GRAY}">{idx+i}</text>')
    if note:
        body.append(f'<text x="{W/2}" y="{H-3}" font-size="9" text-anchor="middle">{escape(note)}</text>')
    Path(out).write_text(_svg(W, H, body), encoding="utf-8")
    return out
