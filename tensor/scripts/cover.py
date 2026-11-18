#!/usr/bin/env python3
"""Tensor 표지 생성기 — 앞표지 · 뒷표지 · 책등 · 인쇄용 펼침면(재단 여백 포함).

    python3 cover.py cover.json -o out/        # out/front.pdf back.pdf spine.pdf spread.pdf (+ .png 미리보기)

cover.json 예시 (assets/cover/cover.example.json 참고):
{
  "brand": "TENSOR",                    교재명 — 앞표지 세로 대형 타이틀
  "subject": "회로이론",                 과목명 — 앞표지 우상단, 책등
  "subject_full": "회로이론및실습",       뒷표지 좌상단 (없으면 subject)
  "subtitle": "시험 개념의 완성",
  "tagline": ["기본부터", "심화까지", "완성하는"],
  "authors": "김준형 · 최재원",
  "school": ["Seoul National", "University"],
  "logo": "snu",                        "snu" = 내장 서울대 흰색 로고(assets/cover/snu_logo_white.svg). 다른 학교는 투명 배경 PNG/SVG 경로
  "cover_color": "#6B3FD4",             ← 바꿀 수 있는 색 1: 표지(도형 그라데이션·하단 띠·포인트)
  "spine_color": "#6B3FD4",             ← 바꿀 수 있는 색 2: 책등 (없으면 cover_color)
  "band": false,                         true = 앞·뒤표지 아래 색 띠(로고·저자를 흰색으로 띠 위에). 기본 false = 띠 없이 흰 바탕, 로고는 표지색
  "type": "serif",                       글꼴 조합: serif(고딕 과목명 + 명조 문구 + Cormorant, 기본) | sans(전부 고딕) | classic(명조 과목명). "fonts" 로 역할별 덮어쓰기
  "pages": 220,                          내지 쪽수 → 책등 두께 자동 계산
  "spine_mm": null,                      제본집이 알려준 두께가 있으면 이 값을 우선
  "symbol": "circuit",                   앞표지 기호: circuit | blocks | tree | <SVG 파일 경로>
  "back_title": ["회로이론 및 실습", "시험 개념의 완성"],
  "back_paras": ["…", "…"]               뒷표지 소개 2문단 (내지 문장을 다듬어 쓴다)
}
색은 cover_color, spine_color 두 개만 바꾼다. 나머지(글자색·배경·레이아웃)는 고정이다.
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import argparse, base64, json, mimetypes, os, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
BUILD = Path(os.environ.get("TENSOR_BUILD", SKILL / ".build")).resolve()
W, H = 794, 1123          # A4 @96dpi
PX_PER_MM = 96 / 25.4
BLEED_MM = 3
INK = "#3A3A42"
SUB = "#44444c"


def spine_mm(cfg):
    if cfg.get("spine_mm"):
        return float(cfg["spine_mm"])
    pages = int(cfg.get("pages") or 200)
    # 80g 모조지 기준 한 장(2쪽) ≈ 0.1mm + 표지·제본 여유 1mm
    return round(pages / 2 * 0.1 + 1.0, 1)


def data_uri(path):
    p = Path(path)
    mt = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mt};base64,{base64.b64encode(p.read_bytes()).decode()}"


BUILTIN_LOGO = {"snu": SKILL / "assets/cover/snu_logo_white.svg"}


def _logo_ratio(path):
    p = Path(path)
    if p.suffix.lower() == ".svg":
        import re
        m = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', p.read_text(encoding="utf-8")[:2000])
        if m:
            return float(m.group(1)) / float(m.group(2))
    try:
        from PIL import Image
        w, h = Image.open(p).size
        return w / h
    except Exception:
        return 1.0


def logo_html(cfg, h, color="#fff"):
    """로고를 한 가지 색으로 칠한다(투명 배경 PNG/SVG의 모양만 쓴다). 띠 위에서는 흰색, 흰 바탕에서는 표지색."""
    if cfg.get("logo") and Path(cfg["logo"]).exists():
        w = h * _logo_ratio(cfg["logo"])
        u = data_uri(cfg["logo"])
        return (f'<div style="height:{h}px;width:{w:.1f}px;background:{color};'
                f'-webkit-mask:url({u}) center/contain no-repeat;mask:url({u}) center/contain no-repeat"></div>')
    return (f'<div style="height:{h}px;width:{h}px;border:1.5px dashed {color};display:flex;'
            f'align-items:center;justify-content:center;font-size:9px;letter-spacing:.1em;color:{color}">LOGO</div>')


# ---------------------------------------------------------------- symbols
GRAD = """
<linearGradient id="fieldA{s}" gradientUnits="userSpaceOnUse" x1="{ax1}" y1="300" x2="{ax2}" y2="860">
  <stop offset="0" style="stop-color:var(--c-050)"/><stop offset="0.45" style="stop-color:var(--c-200)"/><stop offset="1" style="stop-color:var(--c-400)"/>
</linearGradient>
<linearGradient id="fieldB{s}" gradientUnits="userSpaceOnUse" x1="{bx1}" y1="140" x2="{bx2}" y2="1000">
  <stop offset="0" style="stop-color:var(--c-100)"/><stop offset="0.4" style="stop-color:var(--c-300)"/>
  <stop offset="0.75" style="stop-color:var(--c-500)"/><stop offset="1" style="stop-color:var(--c-600)"/>
</linearGradient>"""


def symbol_svg(cfg, dx=0, suffix=""):
    """앞표지 기호. dx 만큼 오른쪽으로 옮겨 그린다(뒷표지에서 이어지는 부분용)."""
    kind = cfg.get("symbol", "circuit")
    g = GRAD.format(s=suffix, ax1=0 + dx, ax2=420 + dx, bx1=460 + dx, bx2=760 + dx)
    A, B = f"url(#fieldA{suffix})", f"url(#fieldB{suffix})"
    if kind == "circuit":   # 커패시터(리드선+두 극판) + 오메가
        body = f"""
<rect x="{500+dx}" y="-10" width="72" height="440" fill="{B}"/>
<rect x="{372+dx}" y="430" width="460" height="76" fill="{B}"/>
<rect x="{372+dx}" y="584" width="460" height="76" fill="{B}"/>
<rect x="{500+dx}" y="660" width="72" height="480" fill="{B}"/>
<circle cx="{110+dx}" cy="560" r="220" fill="{A}"/>
<circle cx="{110+dx}" cy="585" r="88" fill="#fff"/>
<rect x="{84+dx}" y="640" width="52" height="200" fill="#fff"/>
<rect x="{-20+dx}" y="752" width="104" height="58" fill="{A}"/>
<rect x="{136+dx}" y="752" width="196" height="58" fill="{A}"/>"""
    elif kind == "tree":    # 자료구조: 이진 트리(굵은 간선 + 고리 노드)
        def e(x1, y1, x2, y2):
            return f'<line x1="{x1+dx}" y1="{y1}" x2="{x2+dx}" y2="{y2}" stroke="{B}" stroke-width="46" stroke-linecap="round"/>'
        def n(x, y, r, hole):
            return (f'<circle cx="{x+dx}" cy="{y}" r="{r}" fill="{A}"/>'
                    f'<circle cx="{x+dx}" cy="{y}" r="{hole}" fill="#fff"/>')
        body = (e(580, 300, 380, 590) + e(580, 300, 780, 590)
                + e(380, 590, 270, 870) + e(380, 590, 490, 870) + e(780, 590, 700, 870)
                + n(580, 300, 112, 44) + n(380, 590, 98, 38) + n(780, 590, 98, 38)
                + n(270, 870, 84, 32) + n(490, 870, 84, 32) + n(700, 870, 84, 32))
    elif kind == "blocks":  # 과목 무관 기본형: 큰 원 + 계단 막대
        body = f"""
<circle cx="{110+dx}" cy="560" r="230" fill="{A}"/>
<circle cx="{110+dx}" cy="560" r="96" fill="#fff"/>
<rect x="{430+dx}" y="300" width="80" height="840" fill="{B}"/>
<rect x="{540+dx}" y="470" width="80" height="670" fill="{B}"/>
<rect x="{650+dx}" y="640" width="160" height="500" fill="{B}"/>"""
    else:                    # 사용자가 만든 SVG 조각(같은 그라데이션 id 사용)
        frag = Path(kind).read_text(encoding="utf-8")
        body = f'<g transform="translate({dx},0)">{frag.replace("#fieldA", "#fieldA" + suffix).replace("#fieldB", "#fieldB" + suffix)}</g>'
    return f"<defs>{g}</defs>{body}"


# ---------------------------------------------------------------- panels
def _foot(cfg, side):
    """아래 줄: 로고 + 학교(왼쪽), 저자(오른쪽). 띠가 있으면 흰색, 없으면 표지색·먹색."""
    band = cfg.get("band", False)
    school = "<br>".join(cfg.get("school", ["Seoul National", "University"]))
    c_logo = "#fff" if band else "var(--cover)"
    c_school = "#fff" if band else "var(--cover)"
    c_auth = "#fff" if band else INK
    x = 48 if side == "front" else 56
    bar = '<div class="band" style="height:120px"></div>' if band else ""
    return f"""{bar}
  <div class="abs" style="left:{x}px;bottom:36px;display:flex;align-items:center;gap:14px">
    {logo_html(cfg, 50, c_logo)}
    <span class="en-text" style="font-size:16px;line-height:1.15;color:{c_school}">{school}</span>
  </div>
  <div class="abs ko-text" style="right:{x}px;bottom:48px;display:flex;align-items:baseline;gap:10px;font-size:14px;color:{c_auth}">
    <span style="font-weight:600;letter-spacing:.16em">{cfg.get("authors","")}</span><span style="opacity:.75">지음</span>
  </div>"""


def front(cfg):
    tag = "".join(f"<span>{t}</span>" for t in cfg.get("tagline", []))
    offs = [0, 46, 6, 52, 10, 48, 4, 40]
    title = "".join(f'<span style="margin-left:{offs[i % len(offs)]}px">{ch}</span>' for i, ch in enumerate(cfg["brand"]))
    return f"""
<div class="panel" style="width:{W}px;height:{H}px">
  <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" class="abs">{symbol_svg(cfg, 0, "F")}</svg>
  <div class="abs tag ko-text" style="left:50px;top:58px">{tag}</div>
  <div class="abs" style="right:48px;top:50px;display:flex;flex-direction:column;align-items:flex-end;gap:12px">
    <span class="ko-title" style="font-size:32px;color:{INK}">{cfg["subject"]}</span>
    <span class="ko-text" style="font-size:14px;letter-spacing:.2em;margin-right:-.2em;color:{SUB}">{cfg.get("subtitle","")}</span>
  </div>
  <div class="abs brand" style="left:26px;top:257px">{title}</div>
  {_foot(cfg, "front")}
</div>"""


def back(cfg, spine_px):
    paras = "".join(f'<p class="ko-text" style="margin:0;font-size:15px;line-height:1.85;color:{SUB}">{p}</p>' for p in cfg.get("back_paras", []))
    bt = "<br>".join(cfg.get("back_title", [cfg["subject"], cfg.get("subtitle", "")]))
    # 앞표지 왼쪽 밖으로 잘린 도형이 책등을 건너 뒷표지 오른쪽 가장자리로 이어진다
    return f"""
<div class="panel" style="width:{W}px;height:{H}px">
  <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" class="abs">{symbol_svg(cfg, W + spine_px, "B")}</svg>
  <div class="abs" style="left:56px;top:56px;display:flex;flex-direction:column;gap:12px">
    <span class="en-brand" style="font-size:22px;letter-spacing:.34em;color:var(--cover)">{cfg["brand"]}</span>
    <span class="ko-text" style="font-size:13px;letter-spacing:.24em;color:{SUB}">{cfg.get("subject_full", cfg["subject"])}</span>
  </div>
  <div class="abs" style="left:56px;top:330px;width:540px;display:flex;flex-direction:column;gap:28px">
    <h2 class="ko-title" style="margin:0;font-size:36px;line-height:1.35;color:{INK}">{bt}</h2>
    <div style="width:56px;height:4px;background:var(--cover)"></div>
    {paras}
  </div>
  {_foot(cfg, "back")}
</div>"""


def spine(cfg, spine_px):
    narrow = spine_px < 40
    fs_brand, fs_subj = (16, 17) if narrow else (22, 24)
    return f"""
<div class="panel spine" style="width:{spine_px:.2f}px;height:{H}px">
  <div style="writing-mode:vertical-rl;display:flex;align-items:center;gap:22px">
    <span class="en-brand" style="font-size:{fs_brand}px;letter-spacing:.32em">{cfg["brand"]}</span>
    <span style="width:1.5px;height:28px;background:rgba(255,255,255,.6)"></span>
    <span class="ko-head" style="font-size:{fs_subj}px;letter-spacing:.12em">{cfg["subject"]}</span>
    {'' if narrow else f'<span class="ko-text" style="font-size:13px;letter-spacing:.18em;opacity:.9">{cfg.get("subtitle","")}</span>'}
  </div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:20px">
    <span class="ko-text" style="writing-mode:vertical-rl;font-size:12px;font-weight:600;letter-spacing:.2em;opacity:.9">{cfg.get("authors","")}</span>
    {logo_html(cfg, min(38, int(spine_px * 0.66)))}
  </div>
</div>"""


CSS = """
@page {{ margin:0; size:{w}mm {h}mm; }}
:root {{
  --cover:{cover}; --spine:{spine};
  /* 표지색 하나에서 그라데이션 톤을 만든다 — 색을 바꾸면 전부 따라 바뀐다 */
  --c-050:color-mix(in srgb, var(--cover) 12%, #fff);
  --c-100:color-mix(in srgb, var(--cover) 22%, #fff);
  --c-200:color-mix(in srgb, var(--cover) 36%, #fff);
  --c-300:color-mix(in srgb, var(--cover) 58%, #fff);
  --c-400:color-mix(in srgb, var(--cover) 72%, #fff);
  --c-500:color-mix(in srgb, var(--cover) 88%, #fff);
  --c-600:color-mix(in srgb, var(--cover) 82%, #2a3fd0);
}}
html,body{{margin:0;padding:0}}
body{{font-family:'Pretendard',sans-serif;color:#33333b;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.sheet{{width:{w}mm;height:{h}mm;position:relative;overflow:hidden;background:#fff;page-break-after:always}}
.panel{{position:absolute;top:0;overflow:hidden;background:#fff}}
.abs{{position:absolute}}
.tag{{display:flex;flex-direction:column;gap:12px;font-size:17px;letter-spacing:.22em;color:#3A3A42}}
.brand{{display:flex;flex-direction:column;font-size:104px;line-height:1.0;color:#3A3A42;font-family:{en_brand};font-weight:{en_brand_w}}}
.ko-head{{font-family:{ko_head};font-weight:{ko_head_w}}}
.ko-title{{font-family:{ko_head};font-weight:{ko_head_w};letter-spacing:{title_track};margin-right:calc(-1 * {title_track})}}
h2.ko-title{{letter-spacing:calc({title_track} / 3);margin-right:0}}
.ko-text{{font-family:{ko_text};font-weight:{ko_text_w}}}
.en-brand{{font-family:{en_brand};font-weight:{en_brand_w}}}
.en-text{{font-family:{en_text};font-weight:{en_text_w};letter-spacing:.03em}}
.band{{position:absolute;left:0;right:0;bottom:0;background:var(--cover)}}
.spine{{box-sizing:border-box;padding:44px 0 36px;background:linear-gradient(180deg,var(--spine) 0%,color-mix(in srgb,var(--spine) 80%,#2a3fd0) 100%);
  color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:space-between}}
"""


PRET = "'Pretendard',sans-serif"
SERIF = "'Noto Serif KR',serif"
MONT = "'Montserrat','Pretendard',sans-serif"
CORM = "'Cormorant Garamond','Noto Serif KR',serif"
TYPES = {   # 글꼴 조합: 한글 제목(과목명·책등) / 한글 문구·본문 / 영문 대형 브랜드 / 영문 본문(학교명)
    "serif": dict(ko_head=PRET, ko_head_w=700, title_track=".06em", ko_text=SERIF, ko_text_w=600,
                  en_brand=MONT, en_brand_w=800, en_text=CORM, en_text_w=700),
    "sans":  dict(ko_head=PRET, ko_head_w=700, title_track=".06em", ko_text=PRET, ko_text_w=500,
                  en_brand=MONT, en_brand_w=800, en_text=MONT, en_text_w=600),
    "classic": dict(ko_head=SERIF, ko_head_w=700, title_track=".02em", ko_text=SERIF, ko_text_w=600,
                    en_brand=MONT, en_brand_w=800, en_text=CORM, en_text_w=700),
}
FONT_CSS = ["pretendard/dist/web/static/pretendard.css",
            *(f"@fontsource/noto-serif-kr/{w}.css" for w in (500, 600, 700, 900)),
            *(f"@fontsource/montserrat/{w}.css" for w in (600, 800)),
            *(f"@fontsource/cormorant-garamond/{w}.css" for w in (600, 700))]


def sheet(inner_html, w_mm, h_mm, cfg, offset_px=0):
    css = CSS.format(w=w_mm, h=h_mm, cover=cfg.get("cover_color", "#6B3FD4"),
                     spine=cfg.get("spine_color") or cfg.get("cover_color", "#6B3FD4"),
                     **{**TYPES.get(cfg.get("type", "serif"), TYPES["serif"]), **(cfg.get("fonts") or {})})
    links = "".join(f'<link rel="stylesheet" href="{(BUILD / "node_modules" / f).as_uri()}">'
                    for f in FONT_CSS if (BUILD / "node_modules" / f).is_file())
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
{links}<style>{css}</style></head>
<body><div class="sheet">{inner_html}</div></body></html>"""


def build(cfg):
    sp_mm = spine_mm(cfg)
    sp_px = sp_mm * PX_PER_MM
    b = BLEED_MM * PX_PER_MM
    f, bk, s = front(cfg), back(cfg, sp_px), spine(cfg, sp_px)
    import re
    pos = lambda html, x, y=0: re.sub(r'(<div class="panel[^"]*" style=")', lambda m: m.group(1) + f"left:{x:.2f}px;top:{y:.2f}px;", html, count=1)
    docs = {
        "front": sheet(pos(f, 0), 210, 297, cfg),
        "back": sheet(pos(bk, 0), 210, 297, cfg),
        "spine": sheet(pos(s, 0), sp_mm, 297, cfg),
        # 인쇄용 펼침면: 뒷표지 | 책등 | 앞표지, 사방 3mm 재단 여백
        "spread": sheet(pos(bk, b, b) + pos(s, b + W, b) + pos(f, b + W + sp_px, b),
                        round(420 + sp_mm + 2 * BLEED_MM, 2), 297 + 2 * BLEED_MM, cfg),
    }
    return docs, sp_mm


def render_all(docs, out):
    from render import print_sheets
    out.mkdir(parents=True, exist_ok=True)
    print_sheets([(html, out, out / f"{name}.pdf", False) for name, html in docs.items()])
    import pymupdf
    for name in docs:
        d = pymupdf.open(str(out / f"{name}.pdf"))
        d[0].get_pixmap(dpi=60).save(str(out / f"{name}.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("-o", "--out", default="cover")
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    base = Path(a.config).parent
    if cfg.get("logo") in BUILTIN_LOGO:
        cfg["logo"] = str(BUILTIN_LOGO[cfg["logo"]])
    elif cfg.get("logo") and not Path(cfg["logo"]).is_absolute():
        cfg["logo"] = str(base / cfg["logo"])
    if cfg.get("symbol") not in (None, "circuit", "blocks", "tree") and not Path(cfg["symbol"]).is_absolute():
        cfg["symbol"] = str(base / cfg["symbol"])
    if not cfg.get("logo") or not Path(cfg["logo"]).exists():
        print("[안내] 로고 파일이 없어 점선 자리만 표시했습니다. 투명 배경 PNG/SVG 로고를 받아 \"logo\"에 넣으세요.")
    docs, sp = build(cfg)
    render_all(docs, Path(a.out).resolve())
    print(f"책등 두께 {sp}mm ({'지정값' if cfg.get('spine_mm') else str(cfg.get('pages', 200)) + '쪽 기준 자동 계산 — 제본집 실측값으로 바꾸세요'})")
    print("생성:", ", ".join(f"{n}.pdf" for n in docs), "→", a.out)


if __name__ == "__main__":
    main()
