#!/usr/bin/env python3
"""Tensor 교재 HTML → 인쇄용 PDF 렌더러.

사용법:
    python3 render.py book.html                # book.pdf 생성
    python3 render.py book.html -o out.pdf --png previews/   # 쪽별 미리보기 PNG도 생성

HTML 안의 다음 가상 경로를 실제 파일 경로로 바꿔서 렌더링한다.
    tensor://css/        -> <skill>/assets/
    tensor://katex/      -> <build>/node_modules/katex/dist/
    tensor://pretendard/ -> <build>/node_modules/pretendard/dist/web/static/
<build> 는 setup.sh 가 만든 폴더(기본: <skill>/.build)이며 TENSOR_BUILD 환경변수로 바꿀 수 있다.

렌더링 후 각 .page 안에서 아래 여백(본문 하단 한계선)을 넘는 요소가 있으면 경고를 출력한다.
경고가 나오면 해당 쪽 내용을 다음 쪽으로 넘기거나 줄여서 다시 렌더링한다.
"""
import argparse, asyncio, os, shutil, sys, tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
BUILD = Path(os.environ.get("TENSOR_BUILD", SKILL / ".build"))

CHROME_CANDIDATES = [
    os.environ.get("TENSOR_CHROME", ""),
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
]

OVERFLOW_JS = r"""
() => {
  const mm = 96/25.4, out = [];
  document.querySelectorAll('.page').forEach((pg, i) => {
    const pr = pg.getBoundingClientRect();
    const limit = pr.bottom - 24*mm;            // 꼬리말 위 한계선
    let worst = 0;
    pg.querySelectorAll('p,.step,.sol,.concept,.core,.tip,.grade,.vs,.ex,.fig,.qitem,table,.katex-display')
      .forEach(el => {
        if (el.closest('.foot,.fn,.cover,.toc')) return;
        const b = el.getBoundingClientRect().bottom;
        if (b > limit) worst = Math.max(worst, b - limit);
      });
    if (worst > 1) out.push([i+1, Math.round(worst/mm)]);
  });
  return out;
}
"""


def resolve(html: str) -> str:
    katex = (BUILD / "node_modules/katex/dist").as_uri() + "/"
    pret = (BUILD / "node_modules/pretendard/dist/web/static").as_uri() + "/"
    css = (SKILL / "assets").as_uri() + "/"
    return (html.replace("tensor://katex/", katex)
                .replace("tensor://pretendard/", pret)
                .replace("tensor://css/", css))


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    return None  # playwright 내장 chromium 사용


async def main(a):
    from playwright.async_api import async_playwright
    need = [BUILD / "node_modules/katex/dist/katex.min.js", BUILD / "node_modules/pretendard/dist/web/static/pretendard.css"]
    missing = [str(n) for n in need if not n.exists()]
    if missing:
        sys.exit("[오류] 렌더링 자원이 없습니다. 먼저 `bash <skill>/scripts/setup.sh` 를 실행하세요.\n  없음: " + ", ".join(missing))
    src = Path(a.html).resolve()
    tmp = src.with_name(f".{src.stem}.resolved.html")
    tmp.write_text(resolve(src.read_text(encoding="utf-8")), encoding="utf-8")
    out = Path(a.output) if a.output else src.with_suffix(".pdf")
    async with async_playwright() as p:
        kw = {"args": ["--no-sandbox"]}
        ch = find_chrome()
        if ch:
            kw["executable_path"] = ch
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": 900, "height": 1200})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append("JS 오류: " + str(e)))
        await pg.goto(tmp.as_uri())
        try:
            await pg.wait_for_selector("body[data-ready='1']", timeout=20000)
        except Exception:
            print("[경고] KaTeX 렌더 완료 신호를 받지 못했습니다. tensor://katex 경로와 setup.sh 실행 여부를 확인하세요.")
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(600)
        over = await pg.evaluate(OVERFLOW_JS)
        await pg.pdf(path=str(out), prefer_css_page_size=True, print_background=True)
        await b.close()
    tmp.unlink(missing_ok=True)
    print(f"PDF: {out}")
    for e in errs:
        print(f"[브라우저] {e}")
    if over:
        for n, mm in over:
            print(f"[넘침] {n}쪽: 본문이 하단 한계선을 약 {mm}mm 넘었습니다.")
    else:
        print("넘침 없음")
    if a.png:
        import pymupdf
        d = pymupdf.open(str(out))
        Path(a.png).mkdir(parents=True, exist_ok=True)
        for i in range(len(d)):
            d[i].get_pixmap(dpi=a.dpi).save(f"{a.png}/p{i+1:03d}.png")
        print(f"미리보기 PNG {len(d)}장: {a.png}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("-o", "--output")
    ap.add_argument("--png", help="쪽별 미리보기 PNG 폴더")
    ap.add_argument("--dpi", type=int, default=80)
    asyncio.run(main(ap.parse_args()))
