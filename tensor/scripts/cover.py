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
  "pages": 220,                          내지 쪽수 → 책등 두께 자동 계산
  "spine_mm": null,                      제본집이 알려준 두께가 있으면 이 값을 우선
  "symbol": "circuit",                   앞표지 기호: circuit | blocks | <SVG 파일 경로>
  "back_title": ["회로이론 및 실습", "시험 개념의 완성"],
  "back_paras": ["…", "…"]               뒷표지 소개 2문단 (내지 문장을 다듬어 쓴다)
}
색은 cover_color, spine_color 두 개만 바꾼다. 나머지(글자색·배경·레이아웃)는 고정이다.
"""
import argparse, asyncio, base64, json, mimetypes, os, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
BUILD = Path(os.environ.get("TENSOR_BUILD", SKILL / ".build"))
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


def logo_html(cfg, h):
    if cfg.get("logo") and Path(cfg["logo"]).exists():
        return f'<img src="{data_uri(cfg["logo"])}" style="height:{h}px;width:auto;display:block;filter:brightness(0) invert(1)">'
    return (f'<div style="height:{h}px;width:{h}px;border:1.5px dashed rgba(255,255,255,.85);display:flex;'
            f'align-items:center;justify-content:center;font-size:9px;letter-spacing:.1em;color:#fff">LOGO</div>')


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
def front(cfg):
    tag = "".join(f"<span>{t}</span>" for t in cfg.get("tagline", []))
    offs = [0, 46, 6, 52, 10, 48, 4, 40]
    title = "".join(f'<span style="margin-left:{offs[i % len(offs)]}px">{ch}</span>' for i, ch in enumerate(cfg["brand"]))
    school = "<br>".join(cfg.get("school", ["Seoul National", "University"]))
    return f"""
<div class="panel" style="width:{W}px;height:{H}px">
  <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" class="abs">{symbol_svg(cfg, 0, "F")}</svg>
  <div class="abs tag" style="left:48px;top:56px">{tag}</div>
  <div class="abs" style="right:48px;top:52px;display:flex;flex-direction:column;align-items:flex-end;gap:12px">
    <span style="font-size:30px;font-weight:900;letter-spacing:.3em;margin-right:-.3em;color:{INK}">{cfg["subject"]}</span>
    <span style="font-size:13px;letter-spacing:.3em;margin-right:-.3em;color:{SUB}">{cfg.get("subtitle","")}</span>
  </div>
  <div class="abs brand" style="left:26px;top:257px">{title}</div>
  <div class="band" style="height:120px"></div>
  <div class="abs" style="left:48px;bottom:34px;display:flex;align-items:center;gap:12px">
    {logo_html(cfg, 52)}
    <span style="font-size:14px;font-weight:700;letter-spacing:.06em;line-height:1.3;color:#fff">{school}</span>
  </div>
  <div class="abs" style="right:48px;bottom:46px;display:flex;align-items:baseline;gap:10px;font-size:13px;color:#fff">
    <span style="font-weight:500;letter-spacing:.18em">{cfg.get("authors","")}</span><span style="font-weight:300;opacity:.85">지음</span>
  </div>
</div>"""


def back(cfg, spine_px):
    paras = "".join(f'<p style="margin:0;font-size:15px;line-height:1.8;color:{SUB}">{p}</p>' for p in cfg.get("back_paras", []))
    bt = "<br>".join(cfg.get("back_title", [cfg["subject"], cfg.get("subtitle", "")]))
    school = "<br>".join(cfg.get("school", ["Seoul National", "University"]))
    # 앞표지 왼쪽 밖으로 잘린 도형이 책등을 건너 뒷표지 오른쪽 가장자리로 이어진다
    return f"""
<div class="panel" style="width:{W}px;height:{H}px">
  <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" class="abs">{symbol_svg(cfg, W + spine_px, "B")}</svg>
  <div class="abs" style="left:56px;top:56px;display:flex;flex-direction:column;gap:12px">
    <span style="font-size:22px;font-weight:900;letter-spacing:.38em;color:var(--cover)">{cfg["brand"]}</span>
    <span style="font-size:13px;letter-spacing:.3em;color:{SUB}">{cfg.get("subject_full", cfg["subject"])}</span>
  </div>
  <div class="abs" style="left:56px;top:330px;width:540px;display:flex;flex-direction:column;gap:28px">
    <h2 style="margin:0;font-size:36px;font-weight:900;line-height:1.3;letter-spacing:-.01em;color:{INK}">{bt}</h2>
    <div style="width:56px;height:4px;background:var(--cover)"></div>
    {paras}
  </div>
  <div class="band" style="height:120px"></div>
  <div class="abs" style="left:56px;bottom:34px;display:flex;align-items:center;gap:12px">
    {logo_html(cfg, 52)}
    <span style="font-size:14px;font-weight:700;letter-spacing:.06em;line-height:1.3;color:#fff">{school}</span>
  </div>
  <div class="abs" style="right:56px;bottom:46px;display:flex;align-items:baseline;gap:10px;font-size:13px;color:#fff">
    <span style="font-weight:500;letter-spacing:.18em">{cfg.get("authors","")}</span><span style="font-weight:300;opacity:.85">지음</span>
  </div>
</div>"""


def spine(cfg, spine_px):
    narrow = spine_px < 40
    fs_brand, fs_subj = (16, 17) if narrow else (22, 24)
    return f"""
<div class="panel spine" style="width:{spine_px:.2f}px;height:{H}px">
  <div style="writing-mode:vertical-rl;display:flex;align-items:center;gap:22px">
    <span style="font-size:{fs_brand}px;font-weight:900;letter-spacing:.32em">{cfg["brand"]}</span>
    <span style="width:1.5px;height:28px;background:rgba(255,255,255,.6)"></span>
    <span style="font-size:{fs_subj}px;font-weight:900;letter-spacing:.12em">{cfg["subject"]}</span>
    {'' if narrow else f'<span style="font-size:13px;letter-spacing:.18em;opacity:.9">{cfg.get("subtitle","")}</span>'}
  </div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:20px">
    <span style="writing-mode:vertical-rl;font-size:12px;font-weight:500;letter-spacing:.2em;opacity:.9">{cfg.get("authors","")}</span>
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
.tag{{display:flex;flex-direction:column;gap:14px;font-size:15px;letter-spacing:.42em;color:#44444c}}
.brand{{display:flex;flex-direction:column;font-size:108px;font-weight:900;line-height:.98;color:#3A3A42}}
.band{{position:absolute;left:0;right:0;bottom:0;background:var(--cover)}}
.spine{{box-sizing:border-box;padding:44px 0 36px;background:linear-gradient(180deg,var(--spine) 0%,color-mix(in srgb,var(--spine) 80%,#2a3fd0) 100%);
  color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:space-between}}
"""


def sheet(inner_html, w_mm, h_mm, cfg, offset_px=0):
    css = CSS.format(w=w_mm, h=h_mm, cover=cfg.get("cover_color", "#6B3FD4"),
                     spine=cfg.get("spine_color") or cfg.get("cover_color", "#6B3FD4"))
    pret = (BUILD / "node_modules/pretendard/dist/web/static/pretendard.css").as_uri()
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="{pret}"><style>{css}</style></head>
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


async def render_all(docs, out):
    sys.path.insert(0, str(Path(__file__).parent))
    from render import find_chrome
    from playwright.async_api import async_playwright
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        kw = {"args": ["--no-sandbox"]}
        if find_chrome():
            kw["executable_path"] = find_chrome()
        b = await p.chromium.launch(**kw)
        for name, html in docs.items():
            hp = out / f".{name}.html"
            hp.write_text(html, encoding="utf-8")
            pg = await b.new_page()
            await pg.goto(hp.as_uri())
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(300)
            await pg.pdf(path=str(out / f"{name}.pdf"), prefer_css_page_size=True, print_background=True)
            await pg.close()
            hp.unlink()
        await b.close()
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
    if cfg.get("symbol") not in (None, "circuit", "blocks") and not Path(cfg["symbol"]).is_absolute():
        cfg["symbol"] = str(base / cfg["symbol"])
    if not cfg.get("logo") or not Path(cfg["logo"]).exists():
        print("[안내] 로고 파일이 없어 점선 자리만 표시했습니다. 투명 배경 PNG/SVG 로고를 받아 \"logo\"에 넣으세요.")
    docs, sp = build(cfg)
    asyncio.run(render_all(docs, Path(a.out).resolve()))
    print(f"책등 두께 {sp}mm ({'지정값' if cfg.get('spine_mm') else str(cfg.get('pages', 200)) + '쪽 기준 자동 계산 — 제본집 실측값으로 바꾸세요'})")
    print("생성:", ", ".join(f"{n}.pdf" for n in docs), "→", a.out)


if __name__ == "__main__":
    main()
